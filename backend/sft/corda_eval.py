import re
import torch, math
import numpy as np
from tqdm import tqdm
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
    
from transformers import AutoTokenizer, AutoModelForCausalLM
from data_tokenizer import build_tokenizer_dataset
from datasets import load_dataset
import argparse, sys, yaml


# =========================
# PATHS
# =========================
sys.argv = [
    "script.py",
    "--config", "train_config.yml",
]
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

cfg = yaml.safe_load(open(args.config))

CORDA_MODEL_ID = cfg.get("merged_dir", "./sft_merged_model")
TEST_DATA_PATH = "ufone_synthetic_1000.jsonl"

tokenizer = AutoTokenizer.from_pretrained(CORDA_MODEL_ID)

model = AutoModelForCausalLM.from_pretrained(
    CORDA_MODEL_ID,
    device_map="cpu",
    torch_dtype=torch.float32,
)

dataset = load_dataset("json", data_files=TEST_DATA_PATH,
 split="train",)
dataset_for, dataset_tok = build_tokenizer_dataset(dataset, tokenizer, cfg)

# from evaluate import load
# =========================
# 1. SETUP & MODELS
# =========================
# bertscore = load("bertscore")
# Calculate straight line (L2) Euclidean distance
# euclidean_dist = torch.dist(embedding_ref, embedding_pred, p=2).item()

# # sim_score = util.cos_sim(embedding_ref, embedding_pred).item()
# sim_score = 1 / (1 + euclidean_dist)
# semantic_scores.append(sim_score)

# # Extract BERTScore (F1 Semantic Match)
# score_dict = bertscore.compute(predictions=[pred_answer], references=[ref_answer], lang="en")
# sim_score = score_dict["f1"][0]
# semantic_scores.append(sim_score)
        
import re
import json
import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

# =========================
# 1. SETUP & MODELS
# =========================
# Model 1: Symmetric (For Ground Truth vs Prediction)
similarity_model = SentenceTransformer("all-MiniLM-L6-v2")

# Model 2: Asymmetric Q&A (For User Question vs Prediction!)
qa_model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")


from sentence_transformers import CrossEncoder

# This model was specifically trained by Microsoft to grade Question/Answer relevance!
relevance_grader = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def generate_answer_with_confidence(category, question, model, tokenizer, max_new_tokens=256):
    combined_issue = f"Category: {category}\nIssue: {question}"
    prompt = f"<|user|>\n{combined_issue} </s>\n<|assistant|>\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_length = inputs.input_ids.shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,        
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True, 
            output_scores=True,
            return_legacy_cache=False
        )

    # Decode text
    generated_tokens = outputs.sequences[0][input_length:]
    pred_answer = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    # Calculate Confidence
    stacked_scores = torch.stack(outputs.scores, dim=1) 
    probabilities = F.softmax(stacked_scores, dim=-1)
    gen_probs = torch.gather(probabilities, 2, generated_tokens.unsqueeze(0).unsqueeze(-1)).squeeze(-1)
    avg_confidence = gen_probs.mean().item()

    return pred_answer, avg_confidence

# =========================
# 2. PARSERS
# =========================
def extract_route(text):
    match = re.search(r"Route to:\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip().replace('.', '').lower() if match else "unknown"

def extract_decision(text):
    match = re.search(r"Decision:\s*(.*?)(?=\s*Route to:|$)", text, re.IGNORECASE)
    return match.group(1).strip().replace('.', '').lower() if match else "unknown"

# =========================
# 3. MAIN EVALUATION ENGINE
# =========================
def run_evaluation(dataset, model, tokenizer, output_file="evaluation_results.json"):
    y_true_route, y_pred_route = [], []
    y_true_dec, y_pred_dec = [], []
    
    semantic_scores = []
    relevance_scores = []
    confidence_scores = []
    
    category_stats = {}

    for i, ex in enumerate(tqdm(dataset, desc="Evaluating Tickets", unit="ticket", colour="green")):
        category = ex["category"]
        question = ex["question"]
        ref_answer = ex["answer"]

        # Generate answer AND get confidence
        pred_answer, confidence = generate_answer_with_confidence(category, question, model, tokenizer)
        confidence_scores.append(confidence)

        # Extract Routing
        true_route = extract_route(ref_answer)
        pred_route = extract_route(pred_answer)
        is_route_correct = 1 if true_route == pred_route else 0
        y_true_route.append(true_route)
        y_pred_route.append(pred_route)

        # Log Routing Error silently to text file
        if is_route_correct == 0:
            with open("error.log", "a") as log:
                log.write(f"ROUTING MISMATCH in {category}: Expected '{true_route}' but got '{pred_route}'\n")

        # Extract Decision
        true_dec = extract_decision(ref_answer)
        pred_dec = extract_decision(pred_answer)
        is_dec_correct = 1 if true_dec == pred_dec else 0
        y_true_dec.append(true_dec)
        y_pred_dec.append(pred_dec)

        # Log Decision Error silently to text file
        if is_dec_correct == 0:
            with open("error.log", "a") as log:
                log.write(f"DECISION MISMATCH in {category}: Expected '{true_dec}' but got '{pred_dec}'\n")

        # Encode text for similarity metrics
        # embedding_question = similarity_model.encode(question, convert_to_tensor=True)
        embedding_ref = similarity_model.encode(ref_answer, convert_to_tensor=True)
        embedding_pred = similarity_model.encode(pred_answer, convert_to_tensor=True)
        
        # Calculate Semantic Match (Ground Truth vs Prediction)
        sim_score = util.cos_sim(embedding_ref, embedding_pred).item()
        semantic_scores.append(sim_score)

        # --- RELEVANCE MATCH (QnA Embeddings) ---
        # Encode using the specialized Q&A model!
        embedding_q = qa_model.encode(question, convert_to_tensor=True)
        embedding_a = qa_model.encode(pred_answer, convert_to_tensor=True)
        
        # Calculate Cosine Similarity. (We use max(0, score) because cosine can technically 
        # dip slightly below 0, and we don't want negative percentages in our table).
        rel_score = max(0.0, util.cos_sim(embedding_q, embedding_a).item())
        relevance_scores.append(rel_score)
        
        
        # Group by Category
        if category not in category_stats:
            category_stats[category] = {
                "total": 0, "routes_correct": 0, "decs_correct": 0, 
                "sim_scores": [], "rel_scores": [], "conf_scores": []
            }
            
        category_stats[category]["total"] += 1
        category_stats[category]["routes_correct"] += is_route_correct
        category_stats[category]["decs_correct"] += is_dec_correct
        category_stats[category]["sim_scores"].append(sim_score)
        category_stats[category]["rel_scores"].append(rel_score)
        category_stats[category]["conf_scores"].append(confidence)

    # Format and save JSON
    results_payload = display_and_format_results(
        y_true_route, y_pred_route, y_true_dec, y_pred_dec, 
        semantic_scores, relevance_scores, confidence_scores, category_stats
    )
    
    with open(output_file, "w") as f:
        json.dump(results_payload, f, indent=4)
        
    print(f"\n✅ Evaluation Complete. Results saved to {output_file}")

# =========================
# 4. JSON EXPORT ONLY
# =========================
# =========================
# 4. RESULTS DASHBOARD & JSON EXPORT
# =========================
def display_and_format_results(y_true_route, y_pred_route, y_true_dec, y_pred_dec, 
                               semantic_scores, relevance_scores, confidence_scores, category_stats):
    from sklearn.metrics import accuracy_score, precision_score, f1_score
    from rich.console import Console
    from rich.table import Table
    import numpy as np
    
    console = Console()
    
    # 1. Calculate Global Metrics
    route_acc = accuracy_score(y_true_route, y_pred_route) * 100
    route_prec = precision_score(y_true_route, y_pred_route, average="macro", zero_division=0) * 100
    route_f1 = f1_score(y_true_route, y_pred_route, average="macro", zero_division=0) * 100

    dec_acc = accuracy_score(y_true_dec, y_pred_dec) * 100
    dec_prec = precision_score(y_true_dec, y_pred_dec, average="macro", zero_division=0) * 100
    dec_f1 = f1_score(y_true_dec, y_pred_dec, average="macro", zero_division=0) * 100

    global_conf = np.mean(confidence_scores) * 100
    global_rel = np.mean(relevance_scores) * 100
    global_sim = np.mean(semantic_scores) * 100

    # 2. Build the required JSON payload
    json_export = {
        "global_metrics": {
            "model_confidence_percent": round(global_conf, 2),
            "answer_relevance_percent": round(global_rel, 2),
            "answer_semantic_match_percent": round(global_sim, 2),
            "decision_accuracy_percent": round(dec_acc, 2),
            "decision_precision_macro_percent": round(dec_prec, 2),
            "decision_f1_macro_percent": round(dec_f1, 2),
            "routing_accuracy_percent": round(route_acc, 2),
            "routing_precision_macro_percent": round(route_prec, 2),
            "routing_f1_macro_percent": round(route_f1, 2)
        },
        "category_breakdown": {}
    }

    # 3. --- TABLE 1: GLOBAL METRICS ---
    global_table = Table(title="\n🌍 OVERALL MODEL PERFORMANCE", show_header=True, header_style="bold magenta")
    global_table.add_column("Evaluation Metric", width=35)
    global_table.add_column("Score", justify="right", style="bold green")
    
    global_table.add_row("Model Confidence", f"{global_conf:.2f}%")
    global_table.add_row("Answer Relevance (Q vs A)", f"{global_rel:.2f}%")
    global_table.add_row("Semantic Match (Ground Truth)", f"{global_sim:.2f}%")
    global_table.add_section()
    global_table.add_row("Decision Accuracy", f"{dec_acc:.2f}%")
    global_table.add_row("Decision Precision (Macro)", f"{dec_prec:.2f}%")
    global_table.add_row("Decision F1 Score (Macro)", f"{dec_f1:.2f}%")
    global_table.add_section()
    global_table.add_row("Action Accuracy", f"{route_acc:.2f}%")
    global_table.add_row("Action Precision (Macro)", f"{route_prec:.2f}%")
    global_table.add_row("Action F1 Score (Macro)", f"{route_f1:.2f}%")
    console.print(global_table)

    # 4. --- TABLE 2: CATEGORY BREAKDOWN ---
    cat_table = Table(title="\n📊 PERFORMANCE BY TELECOM CATEGORY", show_header=True, header_style="bold cyan")
    cat_table.add_column("Category", width=30)
    cat_table.add_column("Questions", justify="right")
    cat_table.add_column("Decision Accuracy", justify="right", style="bold blue")
    cat_table.add_column("Action Accuracy", justify="right", style="bold yellow")
    cat_table.add_column("Confidnce Score", justify="right")
    cat_table.add_column("Relevance Score", justify="right")
    cat_table.add_column("Similarity Score", justify="right", style="bold green")

    for cat, stats in category_stats.items():
        cat_dec_acc = (stats["decs_correct"] / stats["total"]) * 100
        cat_route_acc = (stats["routes_correct"] / stats["total"]) * 100
        cat_conf = np.mean(stats["conf_scores"]) * 100
        cat_rel = np.mean(stats["rel_scores"]) * 100
        cat_sim = np.mean(stats["sim_scores"]) * 100
        
        cat_table.add_row(
            cat[:28] + ".." if len(cat) > 28 else cat, 
            str(stats["total"]), 
            f"{cat_dec_acc:.1f}%", 
            f"{cat_route_acc:.1f}%", 
            f"{cat_conf:.1f}%",
            f"{cat_rel:.1f}%",
            f"{cat_sim:.1f}%"
        )
        
        json_export["category_breakdown"][cat] = {
            "total_tickets_evaluated": stats["total"],
            "model_confidence_percent": round(cat_conf, 2),
            "answer_relevance_percent": round(cat_rel, 2),
            "answer_semantic_match_percent": round(cat_sim, 2),
            "decision_accuracy_percent": round(cat_dec_acc, 2),
            "routing_accuracy_percent": round(cat_route_acc, 2)
        }
        
    console.print(cat_table)
    return json_export

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    
    # model_path = "./fp_merged"
    # tokenizer = AutoTokenizer.from_pretrained(model_path)
    # merged_model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")
    
    run_evaluation(dataset, model, tokenizer, output_file="evaluation_results.json")
    pass