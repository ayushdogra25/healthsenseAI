// Controller for check.html (Symptom Checker & Prediction Results)

document.addEventListener('DOMContentLoaded', () => {
  // Check API availability and authentication
  if (!api.isAuthenticated()) return;

  // DOM Elements
  const tabDropdown = document.getElementById('tab-dropdown');
  const tabText = document.getElementById('tab-text');
  const tabVoice = document.getElementById('tab-voice');

  const contentDropdown = document.getElementById('content-dropdown');
  const contentText = document.getElementById('content-text');
  const contentVoice = document.getElementById('content-voice');

  const searchInput = document.getElementById('symptom-search-input');
  const resultsList = document.getElementById('symptom-results-list');
  const textInput = document.getElementById('symptoms-text-input');
  const parseTextBtn = document.getElementById('parse-text-btn');

  const voiceRecordBtn = document.getElementById('voice-record-btn');
  const voiceStatus = document.getElementById('voice-status');
  const voiceTranscript = document.getElementById('voice-transcript');

  const tagsContainer = document.getElementById('selected-tags-container');
  const tagsCountEl = document.getElementById('tags-count');
  const clearTagsBtn = document.getElementById('clear-tags-btn');
  const analyzeBtn = document.getElementById('analyze-health-btn');

  const checkerFormSection = document.getElementById('checker-form-section');
  const checkerResultsSection = document.getElementById('checker-results-section');
  const resultsBackBtn = document.getElementById('results-back-btn');

  const symptomsTagsContainer = document.getElementById('results-symptoms-tags');
  const predictionsList = document.getElementById('results-predictions-list');
  const aiExplanationContainer = document.getElementById('results-ai-explanation');

  const riskScoreVal = document.getElementById('risk-score-value');
  const riskSvgProgress = document.getElementById('risk-svg-progress');
  const riskBadge = document.getElementById('risk-badge');
  const riskExplanation = document.getElementById('risk-explanation');

  const saveReportBtn = document.getElementById('save-report-btn');
  const downloadPdfBtn = document.getElementById('download-pdf-btn');

  // State
  let allSymptoms = [];
  let selectedSymptoms = [];
  let currentPredictionId = null;
  let currentPredictionData = null;
  let isRecording = false;
  let recognition = null;

  // Initialize Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRecording = true;
      voiceStatus.textContent = 'Listening... Speak now.';
      voiceStatus.className = 'text-sm font-semibold text-red-500 animate-pulse-soft';
      voiceRecordBtn.className = 'w-20 h-20 rounded-full bg-red-500 text-white flex items-center justify-center text-3xl shadow-lg border border-red-600 transition-all animate-pulse-soft';
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      voiceTranscript.textContent = `"${transcript}"`;
      voiceTranscript.className = 'text-sm text-slate-800 dark:text-slate-200 bg-sky-50 dark:bg-sky-950/20 p-3 rounded-xl min-h-12 w-full flex items-center justify-center border border-sky-300 dark:border-sky-800';
      
      // Auto-parse symptoms from voice transcript
      parseTextAndAddTags(transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      voiceStatus.textContent = `Error: ${event.error}`;
      voiceStatus.className = 'text-sm font-semibold text-red-500';
      resetVoiceButton();
    };

    recognition.onend = () => {
      resetVoiceButton();
    };
  } else {
    voiceStatus.textContent = 'Voice input not supported on this browser.';
    voiceRecordBtn.disabled = true;
    voiceRecordBtn.className = 'w-20 h-20 rounded-full bg-slate-100 text-slate-300 flex items-center justify-center text-3xl cursor-not-allowed border border-slate-200';
  }

  function resetVoiceButton() {
    isRecording = false;
    voiceStatus.textContent = 'Click microphone to start speaking';
    voiceStatus.className = 'text-sm font-semibold text-slate-400';
    voiceRecordBtn.className = 'w-20 h-20 rounded-full bg-red-100 text-red-500 hover:bg-red-200 dark:bg-red-950/30 dark:text-red-400 dark:hover:bg-red-950/50 flex items-center justify-center text-3xl shadow-lg border border-red-200 dark:border-red-900/40 transition-all transform hover:scale-105 active:scale-95 focus:outline-none';
  }

  // Load symptom vocabulary
  loadSymptomVocabulary();

  async function loadSymptomVocabulary() {
    try {
      console.log('[Symptoms] Starting symptom vocabulary load from /api/symptoms-list');
      const symptoms = await api.getSymptomsList();
      allSymptoms = Array.isArray(symptoms) ? symptoms : [];

      console.log('[Symptoms] Loaded into dropdown:', allSymptoms.length);
      console.log('[Symptoms] First few symptoms:', allSymptoms.slice(0, 8));

      if (allSymptoms.length === 0) {
        console.warn('[Symptoms] Symptoms list endpoint returned no items.');
      }
    } catch (err) {
      console.error('[Symptoms] Failed to load symptoms list from /api/symptoms-list:', err);
      showTagFeedback('Unable to load symptom suggestions right now. Please refresh the page.');
    }
  }

  // Tabs logic
  tabDropdown.addEventListener('click', () => switchTab('dropdown'));
  tabText.addEventListener('click', () => switchTab('text'));
  tabVoice.addEventListener('click', () => switchTab('voice'));

  function switchTab(tab) {
    // Reset active tab button
    [tabDropdown, tabText, tabVoice].forEach(btn => {
      btn.className = 'flex-1 py-4 text-slate-500 dark:text-slate-400 hover:text-sky-500 flex justify-center items-center gap-2 focus:outline-none';
    });
    
    // Hide all contents
    [contentDropdown, contentText, contentVoice].forEach(cont => cont.classList.add('hidden'));

    if (tab === 'dropdown') {
      tabDropdown.className = 'flex-1 py-4 text-sky-600 dark:text-sky-400 border-b-2 border-sky-500 flex justify-center items-center gap-2 focus:outline-none';
      contentDropdown.classList.remove('hidden');
    } else if (tab === 'text') {
      tabText.className = 'flex-1 py-4 text-sky-600 dark:text-sky-400 border-b-2 border-sky-500 flex justify-center items-center gap-2 focus:outline-none';
      contentText.classList.remove('hidden');
    } else if (tab === 'voice') {
      tabVoice.className = 'flex-1 py-4 text-sky-600 dark:text-sky-400 border-b-2 border-sky-500 flex justify-center items-center gap-2 focus:outline-none';
      contentVoice.classList.remove('hidden');
    }
  }

  // Search input logic
  searchInput.addEventListener('input', () => {
    const query = searchInput.value.trim().toLowerCase();
    if (!query) {
      resultsList.classList.add('hidden');
      return;
    }

    // Filter symptoms
    const filtered = allSymptoms.filter(sym => sym.toLowerCase().includes(query) && !selectedSymptoms.includes(sym));

    console.log('[Symptoms] Rendering dropdown suggestions:', {
      query,
      totalLoaded: allSymptoms.length,
      visibleCount: filtered.length
    });
    
    if (filtered.length === 0) {
      resultsList.innerHTML = '<div class="p-3 text-slate-400 italic">No symptoms found</div>';
    } else {
      resultsList.innerHTML = filtered.map(sym => `
        <button type="button" class="w-full text-left p-3 hover:bg-sky-50 dark:hover:bg-slate-700/50 transition-colors focus:outline-none">
          ${sym.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </button>
      `).join('');
    }
    
    resultsList.classList.remove('hidden');
  });

  // Handle clicking items in search results
  resultsList.addEventListener('click', (e) => {
    const button = e.target.closest('button');
    if (!button) return;
    
    // Extract raw symptom name
    const selectedSymptomText = button.textContent.trim().toLowerCase();
    
    // Find the original item matching from vocabulary
    const originalSymptom = allSymptoms.find(sym => sym.toLowerCase().replace(/_/g, ' ').trim() === selectedSymptomText);
    
    if (originalSymptom) {
      addSymptom(originalSymptom);
    }
    
    searchInput.value = '';
    resultsList.classList.add('hidden');
  });

  // Close dropdown on click outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsList.contains(e.target)) {
      resultsList.classList.add('hidden');
    }
  });

  // Parse typed text button
  parseTextBtn.addEventListener('click', () => {
    const text = textInput.value.trim();
    if (!text) return;
    parseTextAndAddTags(text);
    textInput.value = '';
  });

  // Parse text helper (used for voice & typing)
  function parseTextAndAddTags(text) {
    // Clean text: remove common conjunctions and punctuation, split by commas or spaces
    const words = text.toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, ' ')
      .replace(/\s+/g, ' ')
      .split(' ');
      
    // Find matching symptoms in vocabulary
    let matchedCount = 0;
    
    // Check multi-word symptoms first (longest match)
    const sortedSymptoms = [...allSymptoms].sort((a, b) => b.length - a.length);
    
    let textLower = text.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, ' ');
    
    sortedSymptoms.forEach(vocabSym => {
      const vocabClean = vocabSym.toLowerCase().replace(/_/g, ' ');
      
      // If the text contains the symptom phrase
      if (textLower.includes(vocabClean)) {
        if (!selectedSymptoms.includes(vocabSym)) {
          addSymptom(vocabSym);
          matchedCount++;
          // Remove from temporary text to prevent double matching substrings
          textLower = textLower.replace(vocabClean, '');
        }
      }
    });

    if (matchedCount > 0) {
      showTagFeedback(`${matchedCount} symptom(s) detected and added!`);
    } else {
      showTagFeedback(`No matching symptoms detected. Try typing different keywords.`);
    }
  }

  function showTagFeedback(msg) {
    // Quick toast alert or temporary notification
    const feedback = document.createElement('div');
    feedback.className = 'fixed bottom-4 right-4 bg-slate-800 text-white px-4 py-2.5 rounded-xl text-xs font-semibold shadow-lg z-50 animate-fade-in';
    feedback.textContent = msg;
    document.body.appendChild(feedback);
    setTimeout(() => {
      feedback.classList.add('opacity-0');
      setTimeout(() => feedback.remove(), 400);
    }, 2000);
  }

  // Voice recording triggers
  voiceRecordBtn.addEventListener('click', () => {
    if (isRecording) {
      recognition.stop();
    } else {
      voiceTranscript.textContent = 'Listening...';
      recognition.start();
    }
  });

  // Clear all tags
  clearTagsBtn.addEventListener('click', () => {
    selectedSymptoms = [];
    renderTags();
  });

  // Add tag
  function addSymptom(sym) {
    if (!selectedSymptoms.includes(sym)) {
      selectedSymptoms.push(sym);
      renderTags();
    }
  }

  // Remove tag
  function removeSymptom(sym) {
    selectedSymptoms = selectedSymptoms.filter(item => item !== sym);
    renderTags();
  }

  // Render tag badges
  function renderTags() {
    tagsCountEl.textContent = selectedSymptoms.length;
    
    if (selectedSymptoms.length === 0) {
      tagsContainer.innerHTML = '<span class="text-xs text-slate-400 self-center">No symptoms selected yet. Use the tabs above to add symptoms.</span>';
      clearTagsBtn.classList.add('hidden');
      return;
    }

    clearTagsBtn.classList.remove('hidden');
    tagsContainer.innerHTML = selectedSymptoms.map(sym => `
      <span class="inline-flex items-center gap-1.5 bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300 pl-3 pr-2 py-1 rounded-xl text-xs font-semibold border border-sky-200/50 dark:border-sky-800/30">
        <span>${sym.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
        <button type="button" class="text-sky-600 hover:text-sky-950 dark:hover:text-white focus:outline-none" onclick="removeTag('${sym}')">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </span>
    `).join('');
  }

  // Expose removeTag globally so onclick handler can access it
  window.removeTag = (sym) => {
    removeSymptom(sym);
  };

  // Analyze Button Click
  analyzeBtn.addEventListener('click', async () => {
    if (selectedSymptoms.length === 0) {
      alert("Please enter at least one symptom to analyze.");
      return;
    }

    const origContent = analyzeBtn.innerHTML;
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fa-solid fa-circle-notch loader-spinner text-lg"></i> Analyzing Symptoms...';

    try {
      const response = await api.predict(selectedSymptoms);
      currentPredictionId = response.prediction_id;
      currentPredictionData = response;
      
      // Render Results Page
      renderResults(response);
      
      // Toggle views
      checkerFormSection.classList.add('hidden');
      checkerResultsSection.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = origContent;
    }
  });

  // Render Results Page Content
  function renderResults(data) {
    // 1. Symptoms List
    symptomsTagsContainer.innerHTML = data.symptoms_entered.map(s => `
      <span class="bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 px-3 py-1 rounded-lg text-xs font-medium border border-slate-200/40 dark:border-slate-600/30">
        ${s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
      </span>
    `).join('');

    // 2. Predictions List
    predictionsList.innerHTML = data.top_diseases.map((pred, idx) => {
      const isTop = idx === 0;
      const barColor = isTop ? 'bg-sky-500' : 'bg-slate-400 dark:bg-slate-600';
      return `
        <div class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="font-bold ${isTop ? 'text-sky-600 dark:text-sky-400' : 'text-slate-600 dark:text-slate-300'}">
              ${idx+1}. ${pred.disease}
            </span>
            <span class="font-bold ${isTop ? 'text-sky-600 dark:text-sky-400' : 'text-slate-500'}">
              ${pred.confidence}%
            </span>
          </div>
          <div class="w-full bg-slate-100 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
            <div class="${barColor} h-full rounded-full transition-all duration-1000 ease-out" style="width: ${pred.confidence}%"></div>
          </div>
        </div>
      `;
    }).join('');

    // 3. Risk Score Circular Ring & Badge
    const score = data.risk_score;
    riskScoreVal.textContent = score;
    
    // Circumference = 390. Score sets the dashoffset.
    const offset = 390 - (390 * score) / 100;
    riskSvgProgress.style.strokeDashoffset = offset;
    
    // Risk Level details
    if (score <= 30) {
      riskBadge.textContent = 'Low Risk';
      riskBadge.className = 'inline-block px-4 py-1.5 rounded-full text-xs font-extrabold uppercase mb-4 tracking-wider bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-400';
      riskSvgProgress.setAttribute('stroke', '#10b981'); // Green
      riskExplanation.textContent = 'Home rest and general precautions should be adequate. Monitor symptoms.';
    } else if (score <= 70) {
      riskBadge.textContent = 'Moderate Risk';
      riskBadge.className = 'inline-block px-4 py-1.5 rounded-full text-xs font-extrabold uppercase mb-4 tracking-wider bg-orange-100 text-orange-800 dark:bg-orange-950/40 dark:text-orange-400';
      riskSvgProgress.setAttribute('stroke', '#f97316'); // Orange
      riskExplanation.textContent = 'Monitor symptoms closely. Seek consultation with a medical professional.';
    } else {
      riskBadge.textContent = 'High Risk';
      riskBadge.className = 'inline-block px-4 py-1.5 rounded-full text-xs font-extrabold uppercase mb-4 tracking-wider bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-400';
      riskSvgProgress.setAttribute('stroke', '#ef4444'); // Red
      riskExplanation.textContent = 'High severity symptoms or disease index. Seek professional medical evaluation promptly.';
    }

    // 4. Gemini Explanation
    aiExplanationContainer.innerHTML = parseMarkdown(data.ai_explanation);
    
    // Save report status button reset
    saveReportBtn.disabled = false;
    saveReportBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Save Report';
  }

  // Simple Markdown Parser
  function parseMarkdown(md) {
    if (!md) return "";
    let html = md;
    
    // Replace headers
    html = html.replace(/^### (.*?)$/gm, '<h4 class="text-base font-bold mt-5 mb-2 text-sky-600 dark:text-sky-400">$1</h4>');
    html = html.replace(/^## (.*?)$/gm, '<h3 class="text-lg font-bold mt-6 mb-2 text-slate-800 dark:text-slate-100">$1</h3>');
    html = html.replace(/^# (.*?)$/gm, '<h2 class="text-xl font-bold mt-8 mb-3 text-slate-800 dark:text-slate-100">$1</h2>');
    
    // Bold text **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-800 dark:text-white">$1</strong>');
    
    // Block quotes and alerts
    html = html.replace(/^>\s+\[!(IMPORTANT|WARNING|CAUTION|NOTE)\]\s*(.*?)$/gm, '<div class="bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500 p-4 my-3 rounded-r-xl text-xs"><span class="font-bold uppercase text-red-700 dark:text-red-400">$1</span>: $2</div>');
    html = html.replace(/^>\s*(.*?)$/gm, '<blockquote class="border-l-4 border-slate-300 dark:border-slate-700 pl-4 italic text-slate-500 my-3">$1</blockquote>');
    
    // Bullet lists
    html = html.replace(/^\*\s+(.*?)$/gm, '<li class="ml-5 list-disc text-sm my-1.5 text-slate-600 dark:text-slate-400">$1</li>');
    html = html.replace(/^-\s+(.*?)$/gm, '<li class="ml-5 list-disc text-sm my-1.5 text-slate-600 dark:text-slate-400">$1</li>');

    // Convert newlines to breaks
    html = html.split('\n').join('<br/>');
    // clean multiple breaks
    html = html.replace(/(<br\/>){3,}/g, '<br/><br/>');
    
    return html;
  }

  // Back Button
  resultsBackBtn.addEventListener('click', () => {
    checkerResultsSection.classList.add('hidden');
    checkerFormSection.classList.remove('hidden');
  });

  // Save Report API trigger
  saveReportBtn.addEventListener('click', async () => {
    if (!currentPredictionId) return;

    saveReportBtn.disabled = true;
    saveReportBtn.innerHTML = '<i class="fa-solid fa-circle-notch loader-spinner"></i> Saving...';

    try {
      const res = await api.generateReport(currentPredictionId);
      alert("Report saved successfully in your profile history!");
      saveReportBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Saved';
    } catch (err) {
      alert("Failed to save report: " + err.message);
      saveReportBtn.disabled = false;
      saveReportBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Save Report';
    }
  });

  // Download PDF Trigger
  downloadPdfBtn.addEventListener('click', async () => {
    if (!currentPredictionId) return;
    
    const origBtn = downloadPdfBtn.innerHTML;
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.innerHTML = '<i class="fa-solid fa-circle-notch loader-spinner"></i> Downloading...';

    try {
      const topDisease = currentPredictionData.top_diseases[0].disease.toLowerCase().replace(/\s+/g, '_');
      const filename = `healthsense_report_${topDisease}_${currentPredictionId}.pdf`;
      await api.downloadReportPDF(currentPredictionId, filename);
    } catch (err) {
      alert("Failed to download report PDF: " + err.message);
    } finally {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.innerHTML = origBtn;
    }
  });
});
