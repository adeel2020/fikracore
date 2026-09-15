"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { useAgenticQna } from "./hooks/useAgenticQna";
import { HistorySidebar } from "./components/HistorySidebar";
import { ChatPanel } from "./components/ChatPanel";
import { TelemetrySidebar } from "./components/TelemetrySidebar";

export function AgenticQnaView() {
  const state = useAgenticQna();

  return (
    <div
      className={cn(
        "relative grid h-[calc(100vh-8rem)] gap-4 overflow-hidden",
        state.showHistory ? "grid-cols-[280px_1fr_360px]" : "grid-cols-[1fr_360px]"
      )}
    >
      <HistorySidebar
        showHistory={state.showHistory}
        setShowHistory={state.setShowHistory}
        handleNewChat={state.handleNewChat}
        sessions={state.sessions}
        pinnedSessionIds={state.pinnedSessionIds}
        sessionPreviews={state.sessionPreviews}
        loadingSessionId={state.loadingSessionId}
        sessionId={state.sessionId}
        loadSession={state.loadSession}
        togglePinSession={state.togglePinSession}
        deleteSession={state.deleteSession}
      />

      <div className="flex flex-col h-full overflow-hidden min-w-0">
        <ChatPanel
          messages={state.messages}
          input={state.input}
          setInput={state.setInput}
          sessionId={state.sessionId}
          loading={state.loading}
          error={state.error}
          backendOnline={state.backendOnline}
          agentMode={state.agentMode}
          activePersona={state.activePersona}
          setActivePersona={state.setActivePersona}
          statusMessage={state.statusMessage}
          structuredResponse={state.structuredResponse}
          activeIncidentId={state.activeIncidentId}
          incidentQueue={state.incidentQueue}
          setActiveIncidentId={state.setActiveIncidentId}
          refreshIncidentQueue={state.refreshIncidentQueue}
          activeIndex={state.activeIndex}
          scrollRef={state.scrollRef}
          inputRef={state.inputRef}
          scrollContainerRef={state.scrollContainerRef}
          handleScroll={state.handleScroll}
          scroll={state.scroll}
          scrollToPage={state.scrollToPage}
          handleSuggestedPrompt={state.handleSuggestedPrompt}
          handlePageChipClick={state.handlePageChipClick}
          handleSubmit={state.handleSubmit}
          handleStop={state.handleStop}
          handleSelectSkill={state.handleSelectSkill}
          handleKeyDown={state.handleKeyDown}
          showSkillsPopup={state.showSkillsPopup}
          filteredSkills={state.filteredSkills}
          selectedSkill={state.selectedSkill}
          setSelectedSkill={state.setSelectedSkill}
          activeSkillIndex={state.activeSkillIndex}
          showHistory={state.showHistory}
          setShowHistory={state.setShowHistory}
        />
      </div>

      <TelemetrySidebar telemetry={state.telemetry} />
    </div>
  );
}
