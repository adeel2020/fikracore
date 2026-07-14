import { useState, useCallback, useEffect, useRef } from 'react';

export function useAudioNarrator() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeChapterId, setActiveChapterId] = useState<number | string | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const stripMarkdown = (text: string) => {
    // Remove headers, bold, italic, list markers, links, etc.
    return text
      .replace(/#/g, '')
      .replace(/\*/g, '')
      .replace(/_/g, '')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/`/g, '')
      .replace(/-/g, '')
      .replace(/={2,}/g, '')
      .trim();
  };

  const play = useCallback((chapterId: number | string, text: string, gender?: 'male' | 'female') => {
    if (!window.speechSynthesis) {
      console.warn('SpeechSynthesis API not supported in this browser.');
      return;
    }

    // Stop current
    window.speechSynthesis.cancel();

    const cleanText = stripMarkdown(text);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utteranceRef.current = utterance;

    // Humanize the voice: Select a premium/natural English voice matching the requested gender
    const voices = window.speechSynthesis.getVoices();
    let preferredVoices = ['Google UK English Female', 'Samantha', 'Karen', 'Tessa', 'Victoria'];
    if (gender === 'male') {
      preferredVoices = ['Google US English', 'Daniel', 'Microsoft David', 'Google UK English Male', 'en-US-Standard-B'];
    } else if (gender === 'female') {
      preferredVoices = ['Google UK English Female', 'Samantha', 'Karen', 'Tessa', 'Victoria', 'Microsoft Zira', 'en-US-Standard-C'];
    }
    
    let selectedVoice = voices.find(v => preferredVoices.includes(v.name));
    if (!selectedVoice) {
      // Fallback filter based on voice gender characteristics in names/languages
      if (gender === 'male') {
        selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Male') || v.name.includes('David') || v.name.includes('Daniel')));
      } else {
        selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Female') || v.name.includes('Zira') || v.name.includes('Samantha')));
      }
    }
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Premium'));
    }
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.startsWith('en'));
    }
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    // Tweak rate and pitch for a more relaxed, humane storytelling tone
    utterance.rate = 0.9;
    utterance.pitch = gender === 'male' ? 0.88 : 0.96;
    
    utterance.onstart = () => {
      setIsPlaying(true);
      setActiveChapterId(chapterId);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setActiveChapterId(null);
    };

    utterance.onerror = (e) => {
      if (e.error !== 'canceled') {
        console.error('Speech synthesis error:', e);
      }
      setIsPlaying(false);
      setActiveChapterId(null);
    };

    window.speechSynthesis.speak(utterance);
  }, []);

  const pause = useCallback(() => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setActiveChapterId(null);
  }, []);

  return {
    play,
    pause,
    isPlaying,
    activeChapterId
  };
}
