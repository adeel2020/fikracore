import re
import asyncio
from collections.abc import AsyncIterator
from crewai import Agent, Task, Crew, Process, LLM
from crewai.agents.tools_handler import ToolsHandler
from crewai.utilities.streaming import (
    StreamChunk,
    StreamChunkType,
    TaskInfo,
    create_async_chunk_generator,
    create_streaming_state,
    signal_end,
    signal_error,
)
from crewai.types.streaming import CrewStreamingOutput
from backend.config import settings

# Modular imports
from backend.agent.complaint.utils import (
    _get_causal_rules,
    _generate_dynamic_agent_intro,
    _generate_dynamic_agent_outro,
)
from backend.agent.complaint.session import (
    _reconstruct_session_state,
    _route_diagnostics,
)
from backend.agent.complaint.formatter import (
    AgentResponse,
    _agent_response_to_dict,
    _format_structured_event,
)
from backend.agent.complaint.tools import (
    active_queues,
    _TOOL_USAGE_STATE,
    _get_tool_usage_state,
    query_causal_knowledge_graph,
    trace_causal_chain,
    diagnose_complaint,
    log_unresolved_complaint,
    gate1_route_complaint,
)

class MobileCustomerComplaintAnalyst:
    def __init__(self):
        pass

    def _create_agent_and_task(self, query: str, user_role: str = "Customer_Ops", streaming: bool = False) -> tuple[Agent, Task, Crew]:
        state = _get_tool_usage_state() or {}
        state["user_role"] = user_role
        _TOOL_USAGE_STATE.set(state)
        llm = LLM(model=settings.openai_model, base_url=settings.openai_api_base, api_key=settings.openai_api_key or "ollama", stream=streaming, temperature=0.0)
        
        # Reset tools' usage counters for each new run
        try:
            query_causal_knowledge_graph.reset_usage_count()
        except Exception:
            pass
        try:
            trace_causal_chain.reset_usage_count()
        except Exception:
            pass
        try:
            diagnose_complaint.reset_usage_count()
        except Exception:
            pass

        agent = Agent(
            role="Customer Complaint Analyst",
            goal="Diagnose the telecom complaint using the causal knowledge graph, evaluate prechecks, and guide the customer operator.",
            backstory=(
                "You are an expert Customer Complaint Analyst. You use the causal knowledge graph to analyze telecom complaints and guide operators."
            ),
            tools=[
                diagnose_complaint,
            ],
            llm=llm,
            tools_handler=ToolsHandler(),
            allow_delegation=False,
            max_iter=3,
            verbose=True,
        )

        if user_role == "Network_Eng":
            role_instructions = (
                "Role: Mobile Core Domain Expert.\n"
                "Tone: Deeply technical, precise.\n"
                "Instructions: In your thoughts and final answer, you MUST detail specific signaling protocol parameters, "
                "protocol interfaces (e.g. SIP, Diameter Gx/Gy/MAP), MML diagnostic check commands (e.g., LST HDYNINFO, LST PQOUTA, LST CSI) "
                "and component nodes (e.g. PCF, nTAS, HSS/UDM, UGW) resolved from the graph."
            )
        elif user_role == "Management":
            role_instructions = (
                "Role: Operations KPI Report Analyst.\n"
                "Tone: Formal, structured, business report format.\n"
                "Instructions: Format the final response as a structured status report containing: \n"
                "  - Incident Summary\n"
                "  - Impacted Core Network System\n"
                "  - SLA Escalation Target Queue\n"
                "  - Next Resolution Path Action Items."
            )
        else:
            role_instructions = (
                "Role: Customer Frontline Assistant.\n"
                "Tone: Simple, clear, conversational, non-technical.\n"
                "Instructions: Focus strictly on explaining the issue in friendly plain language, stating "
                "what handset settings to verify, and indicating where the issue has been routed. "
                "DO NOT output protocol definitions (Diameter, SIP), CLI commands, or technical logs to avoid confusing the operator."
            )

        task_prompt = f"""You are a Customer Complaint Analyst.
    Analyze the user's raw complaint: "{query}"

    AUDIENCE & ROLE RULES:
    {role_instructions}

    DIAGNOSTIC WORKFLOW:
    1. Run the `diagnose_complaint` tool with the complaint query to get the full diagnostic result including prechecks, causal chain paths, and matched intent.
    2. Analyze the diagnostic result and share your reasoning in your thoughts.
    3. Return the final answer after the analysis is completed.

    Provide a highly descriptive, natural, and friendly conversational routing advice.
    Avoid generating a robotic, bullet-pointed, or formulaic checklist. Instead, explain the customer's issue in plain language, explain the findings from the prechecks and dependency checks (e.g. which checks passed or failed) in a smooth narrative flow, and clarify the routing destination with clear next steps.
    Ensure you still populate the fields `assignment_target`, `reassignment_category`, `resolution_category`, and `message` in your structured output.

    You MUST prefix your final response with 'Final Answer: '.
    """

        task = Task(
            description=task_prompt,
            expected_output="A concise plain text conversational routing advice prefixed with 'Final Answer:'.",
            agent=agent,
            output_pydantic=AgentResponse
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
            reasoning=False,
            function_calling_llm=llm,
        )
        
        return agent, task, crew

    def validate_and_route_query(self, query: str) -> str | None:
        q = query.strip()
        if not q:
            return "Please provide a valid query or describe a mobile network customer complaint."

        short_responses = {"yes", "no", "it", "network", "usage", "activation", "prepaid", "postpaid", "1", "2", "3"}
        if q.lower().strip().translate(str.maketrans("", "", '!?.,-')) in short_responses:
            return None

        # Local heuristic checks for symbol-only or gibberish text
        only_symbols = re.sub(r"[\s\d]", "", q)
        if len(only_symbols) > 3 and not any(c.isalnum() for c in only_symbols):
            return "Please describe a mobile network customer complaint or subscriber connectivity issue for troubleshooting assistance."

        cleaned_words_str = re.sub(r"[^a-zA-Z\s]", "", q).strip()
        if cleaned_words_str:
            words = cleaned_words_str.split()
            for word in words:
                w_len = len(word)
                if w_len >= 5:
                    if re.search(r"(.)\1\1", word.lower()):
                        return "Please describe a mobile network customer complaint or subscriber connectivity issue for troubleshooting assistance."
                    vowels = set("aeiouyAEIOUY")
                    v_count = sum(1 for c in word if c in vowels)
                    if v_count == 0:
                        return "Please describe a mobile network customer complaint or subscriber connectivity issue for troubleshooting assistance."
                    if w_len >= 8 and (v_count / w_len) < 0.15:
                        if word.lower() not in {"strengths", "lengths"}:
                            return "Please describe a mobile network customer complaint or subscriber connectivity issue for troubleshooting assistance."
                    consecutive_consonants = 0
                    max_consecutive = 0
                    for c in word.lower():
                        if c not in vowels and c.isalpha():
                            consecutive_consonants += 1
                            if consecutive_consonants > max_consecutive:
                                max_consecutive = consecutive_consonants
                        else:
                            consecutive_consonants = 0
                    if max_consecutive >= 5 and word.lower() not in {"lengths", "strengths", "angstrom"}:
                        return "Please describe a mobile network customer complaint or subscriber connectivity issue for troubleshooting assistance."

        # Check for copy-pasted trace analyzer help messages / commands
        if "trace-analyzer" in q.lower() or "trace analyzer" in q.lower() or q.startswith("### 📊 Trace Analyzer"):
            return (
                "For trace analysis, please use a separate session with the signaling analyst or use the `/trace-analyzer` command in the main chat.\n\n"
                "As the Customer Complaint Analyst, I can only help you troubleshoot subscriber complaints like eSIM registration or voice drops."
            )

        # Check for simple/common generic greetings or off-topic generic help requests
        generic_greetings = {"hi", "hello", "hey", "help", "test", "demo", "status", "who are you", "what can you do"}
        words = q.lower().translate(str.maketrans("", "", '!?.,-')).split()
        if len(words) <= 3 and any(w in generic_greetings for w in words):
            return (
                "Hello! I am the Customer Complaint Analyst.\n\n"
                "I can help troubleshoot subscriber complaints (e.g., eSIM activation failures, voice/data drops, or registration issues).\n\n"
                "Please describe the specific customer issue you would like to investigate."
            )

        # LLM semantic verification for completely off-topic prompts
        try:
            from litellm import completion
            import json
            
            system_prompt = (
                "You are an input validation guardrail system for a Telecom Customer Complaint Analyst.\n"
                "Active Role: Customer Complaint Analyst (Troubleshoots subscriber/customer mobile network complaints like eSIM registration, voice drops, signal loss, data connectivity, and SIM activation).\n\n"
                "Your task is to determine if the user's prompt matches the role of this agent.\n"
                "Set valid to true if the prompt is related to mobile networks, customer complaints, subscriber connectivity, or troubleshooting subscriber issues.\n"
                "Set valid to false if the prompt does not relate to subscriber/customer mobile network complaint troubleshooting (e.g. general questions, writing essays, recipes, unrelated coding, or trace analysis/PCAP signaling parsing which belong to separate analysts).\n\n"
                "Answer ONLY in JSON format: {\"valid\": true} or {\"valid\": false, \"reason\": \"<friendly explanation of why the query is off-topic for a Customer Complaint Analyst, and a redirection to what this agent does (troubleshooting eSIM failures, voice/data drops, or registration issues)>\"}."
            )
            
            response = completion(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": q}
                ],
                temperature=0.0,
                api_key=settings.openai_api_key or "ollama",
                base_url=settings.openai_api_base,
            )
            
            res_content = response.choices[0].message.content
            res_json = json.loads(res_content)
            if not res_json.get("valid", True):
                return res_json.get("reason", "Please provide a valid telecom customer complaint or query.")
        except Exception as e:
            # Fallback to allowing in case of API error
            print(f"[Validation] Semantic validation check skipped: {e}")
            
        return None

    def analyze(self, raw_complaint: str, user_role: str = "Customer_Ops", session_id: str = None) -> str:
        # Run the stream_analyze coroutine and collect all contents to return the full ReAct thoughts and response.
        async def _run():
            chunks = []
            async for chunk in self.stream_analyze(raw_complaint, user_role=user_role, session_id=session_id):
                if chunk.content:
                    chunks.append(chunk.content)
            return "".join(chunks)
        
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(_run(), loop).result()
        except RuntimeError:
            return asyncio.run(_run())

    async def stream_analyze(self, raw_complaint: str, user_role: str = "Customer_Ops", session_id: str = None) -> AsyncIterator[StreamChunk]:
        _TOOL_USAGE_STATE.set({"user_role": user_role})
        
        # Stateful routing context hydration
        session_state = None
        if session_id:
            session_state = _reconstruct_session_state(session_id)
            
            # 1. Intent Classification Chain
            if session_state.get("status") == "INTENT_CLASSIFICATION" and session_state.get("pending_query"):
                clarification = raw_complaint.strip().lower().translate(str.maketrans("", "", '!?.,-'))
                original_q = session_state["pending_query"]
                if clarification in ["yes", "it", "activation", "prepaid", "postpaid", "1", "3"]:
                    raw_complaint = f"{original_q} (user clarified: IT/Activation)"
                else:
                    raw_complaint = f"{original_q} (user clarified: Network/Usage)"
                session_state["status"] = "ANSWERED"
                session_state["pending_query"] = None
                
            # 2. Network Diagnostics Chain
            elif session_state.get("status") == "NETWORK_DIAGNOSTICS" and session_state.get("pending_query"):
                original_q = session_state["pending_query"]
                q_idx = session_state.setdefault("question_index", 1)
                answers = session_state.setdefault("answers", [])
                
                ans_str = raw_complaint.strip().lower().translate(str.maketrans("", "", '!?.,-'))
                ans_val = True
                if ans_str in ["no", "n", "false", "f", "0"]:
                    ans_val = False
                
                answers.append(ans_val)
                
                if q_idx == 1:
                    session_state["question_index"] = 2
                    yield StreamChunk(
                        content="final answer: 2. Are other users in your immediate location experiencing the same issue? (Yes/No)\n",
                        chunk_type=StreamChunkType.TEXT,
                        task_id="complaint_analysis_task",
                        agent_role="Customer Complaint Analyst",
                        agent_id="mcca_diagnostics_q2",
                    )
                    return
                elif q_idx == 2:
                    session_state["question_index"] = 3
                    yield StreamChunk(
                        content="final answer: 3. Have you restarted your device or toggled Airplane mode? (Yes/No)\n",
                        chunk_type=StreamChunkType.TEXT,
                        task_id="complaint_analysis_task",
                        agent_role="Customer Complaint Analyst",
                        agent_id="mcca_diagnostics_q3",
                    )
                    return
                elif q_idx == 3:
                    diagnostics = {
                        "signal": answers[0],
                        "others_affected": answers[1],
                        "restarted": answers[2]
                    }
                    resolved_route = _route_diagnostics(original_q, diagnostics)
                    
                    session_state["status"] = "ANSWERED"
                    session_state["pending_query"] = None
                    session_state.pop("question_index", None)
                    session_state.pop("answers", None)
                    
                    intro_msg = _generate_dynamic_agent_intro(original_q, resolved_route.get("issue_summary", "Unspecified Category"))
                    outro_msg = _generate_dynamic_agent_outro(resolved_route.get("assignment_target", "Assigned Team"))
                    custom_msg = resolved_route.get("message", "")
                    
                    for line in (intro_msg + "\n\n").splitlines(keepends=True):
                        yield StreamChunk(
                            content=line,
                            chunk_type=StreamChunkType.TEXT,
                            task_id="complaint_analysis_task",
                            agent_role="Customer Complaint Analyst",
                            agent_id="mcca_structured",
                        )
                        await asyncio.sleep(0.03)

                    structured_text = _format_structured_event(resolved_route, query=original_q)
                    for line in structured_text.splitlines(keepends=True):
                        yield StreamChunk(
                            content=line,
                            chunk_type=StreamChunkType.TEXT,
                            task_id="complaint_analysis_task",
                            agent_role="Customer Complaint Analyst",
                            agent_id="mcca_structured",
                        )
                        await asyncio.sleep(0.03)

                    final_outro_content = "\nfinal answer: "
                    if custom_msg:
                        final_outro_content += f"{custom_msg}\n\n"
                    final_outro_content += f"{outro_msg}\n"
                    
                    for line in final_outro_content.splitlines(keepends=True):
                        yield StreamChunk(
                            content=line,
                            chunk_type=StreamChunkType.TEXT,
                            task_id="complaint_analysis_task",
                            agent_role="Customer Complaint Analyst",
                            agent_id="mcca_structured",
                        )
                        await asyncio.sleep(0.03)
                    return

        redirect_message = self.validate_and_route_query(raw_complaint)
        if redirect_message:
            yield StreamChunk(
                content=redirect_message,
                chunk_type=StreamChunkType.TEXT,
                task_id="complaint_analysis_validation_failed",
                agent_role="System Validator",
                agent_id="mcca_validation_failed"
            )
            return

        # ── Gate 1: Deterministic routing (< 5ms) ──────────────────────────
        gate1_result = gate1_route_complaint(raw_complaint)
        if gate1_result.get("confident", False):
            if gate1_result.get("matched_node_id") == "tie_clarification" or "clarify" in gate1_result.get("resolution_category", "").lower():
                if session_state:
                    session_state["status"] = "INTENT_CLASSIFICATION"
                    session_state["pending_query"] = raw_complaint
            elif str(gate1_result.get("matched_node_id")).startswith("fallback_") and gate1_result.get("reassignment_category") == "Usage":
                if session_state:
                    session_state["status"] = "NETWORK_DIAGNOSTICS"
                    session_state["pending_query"] = raw_complaint
                    session_state["question_index"] = 1
                    session_state["answers"] = []
            else:
                if session_state:
                    session_state["status"] = "ANSWERED"
                    session_state["pending_query"] = None
            is_final_route = not (
                gate1_result.get("matched_node_id") == "tie_clarification" or 
                "clarify" in gate1_result.get("resolution_category", "").lower() or
                str(gate1_result.get("matched_node_id")).startswith("fallback_")
            )

            if is_final_route:
                intro_msg = _generate_dynamic_agent_intro(raw_complaint, gate1_result.get("issue_summary", "Unspecified Category"))
                outro_msg = _generate_dynamic_agent_outro(gate1_result.get("assignment_target", "Assigned Team"))
                
                for line in (intro_msg + "\n\n").splitlines(keepends=True):
                    yield StreamChunk(
                        content=line,
                        chunk_type=StreamChunkType.TEXT,
                        task_id="complaint_analysis_task",
                        agent_role="Customer Complaint Analyst",
                        agent_id="mcca_structured",
                    )
                    await asyncio.sleep(0.03)

            structured_text = _format_structured_event(gate1_result, query=raw_complaint)
            for line in structured_text.splitlines(keepends=True):
                yield StreamChunk(
                    content=line,
                    chunk_type=StreamChunkType.TEXT,
                    task_id="complaint_analysis_task",
                    agent_role="Customer Complaint Analyst",
                    agent_id="mcca_structured",
                )
                await asyncio.sleep(0.03)

            if is_final_route:
                for line in (f"\nfinal answer: {outro_msg}\n").splitlines(keepends=True):
                    yield StreamChunk(
                        content=line,
                        chunk_type=StreamChunkType.TEXT,
                        task_id="complaint_analysis_task",
                        agent_role="Customer Complaint Analyst",
                        agent_id="mcca_structured",
                    )
                    await asyncio.sleep(0.03)
            return

        # ── Gate 2: Full LLM-backed RCA (merged diagnose_complaint tool) ──
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        active_queues[raw_complaint] = (queue, loop)

        try:
            _TOOL_USAGE_STATE.set({"user_role": user_role})
            agent, task, crew = self._create_agent_and_task(raw_complaint, user_role=user_role, streaming=True)
            
            task_info: TaskInfo = {
                "index": 0,
                "name": "complaint_analysis",
                "id": "complaint_analysis_task",
                "agent_role": "Customer Complaint Analyst",
                "agent_id": "mcca",
            }
            result_holder: list[str] = []
            output_holder: list[CrewStreamingOutput] = []
            structured_result: dict = {}

            state = create_streaming_state(
                current_task_info=task_info,
                result_holder=result_holder,
                use_async=True,
            )

            async def run_and_signal():
                try:
                    res = None
                    try:
                        res = await crew.kickoff_async()
                    except Exception as e:
                        print(f"[KnowledgeGraphRetriever] Crew execution failed or validation failed: {e}")
                        structured_result.clear()
                        structured_result.update({
                            "issue_summary": f"Telecom complaint: {raw_complaint}",
                            "mandatory_prechecks": [],
                            "depends_on": [],
                            "assignment_target": "SOC Mobile Core Support",
                            "reassignment_category": "Unresolved",
                            "resolution_category": "General Fallback",
                            "message": "I encountered an formatting issue while routing this complaint. Assigned to the fallback core support team."
                        })
                        return structured_result

                    parsed = None
                    try:
                        parsed = res.tasks_output[0].pydantic
                    except Exception:
                        parsed = None
                    structured_result.clear()
                    structured_result.update(_agent_response_to_dict(parsed))
                    return structured_result
                except Exception as e:
                    signal_error(state, e, is_async=True)
                    raise
                finally:
                    signal_end(state, is_async=True)

            async def pump_crew_chunks():
                try:
                    async for chunk in create_async_chunk_generator(
                        state=state,
                        run_coro=run_and_signal,
                        output_holder=output_holder,
                    ):
                        await queue.put(chunk)
                    if structured_result:
                        is_tie = (
                            structured_result.get("matched_node_id") == "tie_clarification" or 
                            "clarify" in structured_result.get("resolution_category", "").lower() or
                            structured_result.get("assignment_target") == "pending_user_input"
                        )
                        is_fallback = (
                            str(structured_result.get("matched_node_id", "")).startswith("fallback_") and
                            structured_result.get("reassignment_category") == "Usage"
                        )
                        if is_tie:
                            if session_state:
                                session_state["status"] = "INTENT_CLASSIFICATION"
                                session_state["pending_query"] = raw_complaint
                        elif is_fallback:
                            if session_state:
                                session_state["status"] = "NETWORK_DIAGNOSTICS"
                                session_state["pending_query"] = raw_complaint
                                session_state["question_index"] = 1
                                session_state["answers"] = []
                        else:
                            if session_state:
                                session_state["status"] = "ANSWERED"
                                session_state["pending_query"] = None
                        await queue.put(
                            StreamChunk(
                                content=_format_structured_event(structured_result, query=raw_complaint),
                                chunk_type=StreamChunkType.TEXT,
                                task_id="complaint_analysis_task",
                                agent_role="Customer Complaint Analyst",
                                agent_id="mcca_structured",
                            )
                        )
                except Exception as e:
                    await queue.put(e)
                finally:
                    await queue.put(None)

            asyncio.create_task(pump_crew_chunks())

            suppress_llm_generation = False
            accumulated_buffer = ""

            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                
                chunk = item

                if chunk.agent_id in ["mcca_observation", "mcca_structured"]:
                    suppress_llm_generation = False
                    accumulated_buffer = ""
                    yield chunk
                    continue

                if suppress_llm_generation:
                    continue

                if chunk.content:
                    accumulated_buffer += chunk.content

                    if "Action Input:" in accumulated_buffer:
                        action_input_idx = accumulated_buffer.find("Action Input:")
                        json_start = accumulated_buffer.find("{", action_input_idx)
                        if json_start != -1:
                            brace_count = 0
                            json_end = -1
                            for i in range(json_start, len(accumulated_buffer)):
                                if accumulated_buffer[i] == '{':
                                    brace_count += 1
                                elif accumulated_buffer[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i
                                        break
                            
                            if json_end != -1:
                                prev_len = len(accumulated_buffer) - len(chunk.content)
                                chunk_end_idx = json_end - prev_len
                                
                                clean_chunk_content = chunk.content[:chunk_end_idx + 1]
                                yield StreamChunk(
                                    content=clean_chunk_content,
                                    chunk_type=chunk.chunk_type,
                                    task_id=chunk.task_id,
                                    agent_role=chunk.agent_role,
                                    agent_id=chunk.agent_id
                                )
                                suppress_llm_generation = True
                                accumulated_buffer = ""
                                continue

                    if "Observation:" in accumulated_buffer:
                        obs_idx = accumulated_buffer.find("Observation:")
                        prev_len = len(accumulated_buffer) - len(chunk.content)
                        chunk_obs_idx = obs_idx - prev_len
                        
                        clean_chunk_content = chunk.content[:chunk_obs_idx] if chunk_obs_idx > 0 else ""
                        if clean_chunk_content:
                            yield StreamChunk(
                                content=clean_chunk_content,
                                chunk_type=chunk.chunk_type,
                                task_id=chunk.task_id,
                                agent_role=chunk.agent_role,
                                agent_id=chunk.agent_id
                            )
                        suppress_llm_generation = True
                        accumulated_buffer = ""
                        continue

                yield chunk
        finally:
            active_queues.pop(raw_complaint, None)

# Singleton Instance
complaint_analyst = MobileCustomerComplaintAnalyst()
