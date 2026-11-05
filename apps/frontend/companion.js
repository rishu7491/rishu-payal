/**
 * Payal Dynamic Robot Companion & Emotion Engine
 * Handles 60fps Canvas Robot Face, Eye Tracking, Blinking,
 * Real-time Audio Lip-Sync, and Emotional Voice Modulation.
 */

class RobotCompanion {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.width = this.canvas ? this.canvas.width : 200;
    this.height = this.canvas ? this.canvas.height : 200;

    // Emotional State: neutral, happy, proud, excited, serious, sad, thinking, alert
    this.emotion = 'neutral';
    this.emotionIntensity = 0.8;

    // Facial Animation Variables
    this.eyeTargetX = 0;
    this.eyeTargetY = 0;
    this.eyeCurrentX = 0;
    this.eyeCurrentY = 0;
    this.blinkProgress = 0; // 0 = open, 1 = closed
    this.isBlinking = false;
    this.lastBlinkTime = performance.now();
    this.blinkInterval = 3200;

    // Speaking & Lip-Sync Variables
    this.isSpeaking = false;
    this.mouthOpen = 0;
    this.audioLevel = 0;
    this.orbitAngle = 0;

    // Web Audio API
    this.audioContext = null;
    this.analyser = null;
    this.audioData = new Uint8Array(32);

    // Speech Synthesis & Recognition
    this.synth = window.speechSynthesis;
    this.selectedVoice = null;
    this.recognition = null;
    this.isListening = false;
    this.onSpeechResult = null;
    this.onEmotionChange = null;

    this.initAudioAndSpeech();
    this.initEventListeners();
    this.animate();
  }

  initVoice() {
    if (!this.synth) return;
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return;

    // Preference: 1. Natural/Online Indian voices, 2. Hindi, 3. Indian English, 4. Natural English
    const naturalIndian = voices.find(v => {
      const name = v.name.toLowerCase();
      const lang = (v.lang || '').toLowerCase();
      const isIndian = lang.includes('hi') || lang.includes('in');
      const isNatural = name.includes('natural') || name.includes('online') || name.includes('google') || name.includes('swara');
      return isIndian && isNatural;
    });

    const anyHindi = voices.find(v => (v.lang || '').toLowerCase().startsWith('hi'));
    const anyIndian = voices.find(v => (v.lang || '').toLowerCase().includes('in') || v.name.toLowerCase().includes('india') || v.name.toLowerCase().includes('neerja'));
    const anyNatural = voices.find(v => v.name.toLowerCase().includes('natural') || v.name.toLowerCase().includes('google'));

    this.selectedVoice = naturalIndian || anyHindi || anyIndian || anyNatural || voices[0];
  }

  initAudioAndSpeech() {
    if (this.synth) {
      this.initVoice();
      if (typeof this.synth.onvoiceschanged !== 'undefined') {
        this.synth.onvoiceschanged = () => this.initVoice();
      }
    }

    // Initialize Web Speech Recognition if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'hi-IN'; // Default Hinglish/Hindi & English friendly

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        if (this.onSpeechResult) {
          this.onSpeechResult(transcript, event.results[0].isFinal);
        }
      };

      this.recognition.onend = () => {
        this.isListening = false;
        const micBtn = document.getElementById('btnMicToggle');
        if (micBtn) micBtn.classList.remove('active');
      };
    }
  }

  initEventListeners() {
    // Eye tracking: mouse movement
    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dx = (e.clientX - centerX) / (window.innerWidth / 2);
      const dy = (e.clientY - centerY) / (window.innerHeight / 2);
      this.eyeTargetX = Math.max(-1, Math.min(1, dx)) * 14;
      this.eyeTargetY = Math.max(-1, Math.min(1, dy)) * 10;
    });

    // Touch support for phone tracking
    window.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) {
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const dx = (touch.clientX - centerX) / (window.innerWidth / 2);
        const dy = (touch.clientY - centerY) / (window.innerHeight / 2);
        this.eyeTargetX = Math.max(-1, Math.min(1, dx)) * 14;
        this.eyeTargetY = Math.max(-1, Math.min(1, dy)) * 10;
      }
    });
  }

  setEmotion(newEmotion, intensity = 0.8) {
    this.emotion = newEmotion.toLowerCase();
    this.emotionIntensity = intensity;

    // Update UI badge
    const badge = document.getElementById('emotionBadge');
    if (badge) {
      badge.textContent = this.emotion.toUpperCase();
      badge.className = `emotion-tag-pill ${this.emotion}`;
    }

    if (this.onEmotionChange) {
      this.onEmotionChange(this.emotion, intensity);
    }
  }

  toggleListening() {
    if (!this.recognition) {
      alert('Speech Recognition is not supported by your browser.');
      return;
    }
    if (this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    } else {
      try {
        this.recognition.start();
        this.isListening = true;
      } catch (err) {
        console.warn('Recognition start error:', err);
      }
    }
    const micBtn = document.getElementById('btnMicToggle');
    if (micBtn) micBtn.classList.toggle('active', this.isListening);
  }

  prepareTextForSpeech(text) {
    if (!text) return '';
    // Strip code blocks
    let clean = text.replace(/```[\s\S]*?```/g, 'मैंने कोड तैयार कर दिया है।');
    // Strip URLs
    clean = clean.replace(/https?:\/\/\S+/g, '');
    // Strip markdown formatting symbols
    clean = clean.replace(/[*#`_\[\]()]/g, ' ');
    // Strip system disclaimers or trailing metadata
    clean = clean.replace(/---\s*\*Skipped:[\s\S]*$/gi, '');
    clean = clean.replace(/\*Skipped:[^\*]*\*/gi, '');
    clean = clean.replace(/\*Risk:[^\*]*\*/gi, '');
    clean = clean.replace(/MOOD:\s*\w+/gi, '');
    // Normalize spaces
    clean = clean.replace(/\s+/g, ' ').trim();

    // Limit voice speech to conversational sentences (first 2-3 sentences max)
    const sentences = clean.split(/(?<=[.?!।])\s+/);
    if (sentences.length > 3) {
      clean = sentences.slice(0, 3).join(' ');
    }
    return clean;
  }

  speak(text, emotion = null) {
    if (!this.synth) return;
    if (emotion) this.setEmotion(emotion);

    this.synth.cancel(); // Stop prior utterance

    const speechText = this.prepareTextForSpeech(text);
    if (!speechText) return;

    const utterance = new SpeechSynthesisUtterance(speechText);
    if (!this.selectedVoice) this.initVoice();
    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
      utterance.lang = this.selectedVoice.lang || 'hi-IN';
    } else {
      utterance.lang = 'hi-IN';
    }

    // Natural, Human-Like Voice Modulation (not cartoonish/robotic)
    switch (this.emotion) {
      case 'happy':
      case 'excited':
        utterance.pitch = 1.04;
        utterance.rate = 1.05;
        break;
      case 'proud':
        utterance.pitch = 1.02;
        utterance.rate = 1.02;
        break;
      case 'sad':
        utterance.pitch = 0.95;
        utterance.rate = 0.92;
        break;
      case 'serious':
        utterance.pitch = 0.98;
        utterance.rate = 0.98;
        break;
      case 'thinking':
        utterance.pitch = 1.0;
        utterance.rate = 1.0;
        break;
      default:
        utterance.pitch = 1.0;
        utterance.rate = 1.02;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.mouthOpen = 0;
      this.audioLevel = 0;
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
    };

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
      this.isSpeaking = false;
      this.mouthOpen = 0;
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.update();
    this.render();
  }

  update() {
    const now = performance.now();

    // 1. Smooth eye movement interpolation
    this.eyeCurrentX += (this.eyeTargetX - this.eyeCurrentX) * 0.12;
    this.eyeCurrentY += (this.eyeTargetY - this.eyeCurrentY) * 0.12;

    // 2. Blinking cycle
    if (!this.isBlinking && now - this.lastBlinkTime > this.blinkInterval) {
      this.isBlinking = true;
      this.lastBlinkTime = now;
      this.blinkInterval = 2800 + Math.random() * 2500;
    }

    if (this.isBlinking) {
      this.blinkProgress += 0.22;
      if (this.blinkProgress >= Math.PI) {
        this.blinkProgress = 0;
        this.isBlinking = false;
      }
    }

    // 3. Speaking / Lip-sync simulation
    if (this.isSpeaking) {
      this.audioLevel = 0.3 + 0.7 * Math.abs(Math.sin(now * 0.015) * Math.cos(now * 0.009));
      this.mouthOpen += (this.audioLevel - this.mouthOpen) * 0.3;
    } else {
      this.mouthOpen *= 0.8;
      this.audioLevel = 0;
    }

    // 4. Update equalizer bars in DOM if present
    const eqBars = document.querySelectorAll('.eq-bar');
    if (eqBars.length > 0) {
      eqBars.forEach((bar, idx) => {
        const height = this.isSpeaking
          ? 3 + Math.sin(now * 0.01 + idx) * 10 * this.audioLevel
          : 2;
        bar.style.height = `${Math.max(2, Math.min(16, height))}px`;
      });
    }

    // 5. Rotation angle for thinking state
    this.orbitAngle += 0.04;
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const cx = this.width / 2;
    const cy = this.height / 2;

    ctx.clearRect(0, 0, this.width, this.height);

    // Emotion Color Palettes
    let primaryGlow = '#38bdf8'; // Default cyan
    let secondaryGlow = '#818cf8';
    if (this.emotion === 'happy') {
      primaryGlow = '#34d399'; // Emerald
      secondaryGlow = '#38bdf8';
    } else if (this.emotion === 'proud') {
      primaryGlow = '#fbbf24'; // Golden amber
      secondaryGlow = '#f59e0b';
    } else if (this.emotion === 'excited') {
      primaryGlow = '#a855f7'; // Purple neon
      secondaryGlow = '#38bdf8';
    } else if (this.emotion === 'serious') {
      primaryGlow = '#60a5fa'; // Laser blue
      secondaryGlow = '#1e3a8a';
    } else if (this.emotion === 'sad') {
      primaryGlow = '#818cf8'; // Soft indigo
      secondaryGlow = '#475569';
    } else if (this.emotion === 'alert') {
      primaryGlow = '#f87171'; // Coral red
      secondaryGlow = '#fbbf24';
    }

    // 1. Outer Halo / Ambient Neon Glow
    const haloRadius = 78 + (this.isSpeaking ? this.mouthOpen * 6 : 0);
    const gradHalo = ctx.createRadialGradient(cx, cy, 55, cx, cy, haloRadius);
    gradHalo.addColorStop(0, primaryGlow + '33');
    gradHalo.addColorStop(1, 'transparent');
    ctx.fillStyle = gradHalo;
    ctx.beginPath();
    ctx.arc(cx, cy, haloRadius, 0, Math.PI * 2);
    ctx.fill();

    // 2. Robot Head Chassis (Rounded Helmet)
    ctx.save();
    ctx.fillStyle = '#0d1527';
    ctx.strokeStyle = primaryGlow;
    ctx.lineWidth = 3;
    ctx.shadowColor = primaryGlow;
    ctx.shadowBlur = 12;

    ctx.beginPath();
    this.roundRect(ctx, cx - 72, cy - 62, 144, 124, 38);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // 3. Digital Glass Visor
    ctx.save();
    const gradVisor = ctx.createLinearGradient(cx, cy - 45, cx, cy + 45);
    gradVisor.addColorStop(0, '#060a12');
    gradVisor.addColorStop(1, '#0b1220');
    ctx.fillStyle = gradVisor;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    this.roundRect(ctx, cx - 58, cy - 44, 116, 88, 24);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // 4. Eyes Rendering (Dynamic Emotion Shapes + Blinking)
    const blinkScale = 1 - Math.sin(this.blinkProgress);
    const leftEyeX = cx - 26 + this.eyeCurrentX;
    const rightEyeX = cx + 26 + this.eyeCurrentX;
    const eyeY = cy - 8 + this.eyeCurrentY;

    ctx.save();
    ctx.fillStyle = primaryGlow;
    ctx.shadowColor = primaryGlow;
    ctx.shadowBlur = 14;

    if (this.emotion === 'thinking') {
      // Rotating Orbital Rings
      this.drawThinkingEye(ctx, leftEyeX, eyeY, 12, this.orbitAngle);
      this.drawThinkingEye(ctx, rightEyeX, eyeY, 12, -this.orbitAngle);
    } else if (this.emotion === 'happy') {
      // Crescent Smiling Arcs
      this.drawHappyEye(ctx, leftEyeX, eyeY, 15, blinkScale);
      this.drawHappyEye(ctx, rightEyeX, eyeY, 15, blinkScale);
    } else if (this.emotion === 'proud') {
      // Radiant Star / High Crest
      this.drawProudEye(ctx, leftEyeX, eyeY, 14, blinkScale);
      this.drawProudEye(ctx, rightEyeX, eyeY, 14, blinkScale);
    } else if (this.emotion === 'serious') {
      // Sharp Focused Slits
      this.drawSeriousEye(ctx, leftEyeX, eyeY, 16, blinkScale);
      this.drawSeriousEye(ctx, rightEyeX, eyeY, 16, blinkScale);
    } else if (this.emotion === 'sad') {
      // Drooping Gentle Eyes
      this.drawSadEye(ctx, leftEyeX, eyeY, 13, blinkScale);
      this.drawSadEye(ctx, rightEyeX, eyeY, 13, blinkScale);
    } else {
      // Neutral Friendly Ovals
      this.drawNeutralEye(ctx, leftEyeX, eyeY, 14, 18 * blinkScale);
      this.drawNeutralEye(ctx, rightEyeX, eyeY, 14, 18 * blinkScale);
    }
    ctx.restore();

    // 5. Mouth & Lip-Sync Waveform
    ctx.save();
    ctx.strokeStyle = primaryGlow;
    ctx.fillStyle = primaryGlow;
    ctx.shadowColor = primaryGlow;
    ctx.shadowBlur = 8;
    ctx.lineWidth = 2.5;

    const mouthY = cy + 24;
    const mouthW = 28 + this.mouthOpen * 8;
    const mouthH = 3 + this.mouthOpen * 12;

    if (this.isSpeaking) {
      ctx.beginPath();
      ctx.ellipse(cx, mouthY, mouthW / 2, mouthH / 2, 0, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.emotion === 'happy') {
      ctx.beginPath();
      ctx.arc(cx, mouthY - 4, 14, 0.2 * Math.PI, 0.8 * Math.PI, false);
      ctx.stroke();
    } else if (this.emotion === 'sad') {
      ctx.beginPath();
      ctx.arc(cx, mouthY + 10, 14, 1.2 * Math.PI, 1.8 * Math.PI, false);
      ctx.stroke();
    } else {
      // Gentle straight calm smile
      ctx.beginPath();
      ctx.moveTo(cx - 10, mouthY);
      ctx.lineTo(cx + 10, mouthY);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawNeutralEye(ctx, x, y, radiusX, radiusY) {
    if (radiusY <= 1) {
      // Blink line
      ctx.fillRect(x - radiusX, y - 1, radiusX * 2, 2);
      return;
    }
    ctx.beginPath();
    ctx.ellipse(x, y, radiusX, Math.max(1, radiusY), 0, 0, Math.PI * 2);
    ctx.fill();

    // Inner Pupil Sparkle
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x - radiusX * 0.3, y - radiusY * 0.3, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  drawHappyEye(ctx, x, y, size, blinkScale) {
    ctx.lineWidth = 4 * Math.max(0.2, blinkScale);
    ctx.beginPath();
    ctx.arc(x, y + 4, size, Math.PI * 1.15, Math.PI * 1.85, false);
    ctx.stroke();
  }

  drawProudEye(ctx, x, y, size, blinkScale) {
    ctx.beginPath();
    ctx.ellipse(x, y, size, size * 0.7 * Math.max(0.2, blinkScale), 0, 0, Math.PI * 2);
    ctx.fill();

    // Star sparkle
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  drawSeriousEye(ctx, x, y, size, blinkScale) {
    const h = 4 * Math.max(0.2, blinkScale);
    ctx.fillRect(x - size, y - h / 2, size * 2, h);
  }

  drawSadEye(ctx, x, y, size, blinkScale) {
    ctx.lineWidth = 3.5 * Math.max(0.2, blinkScale);
    ctx.beginPath();
    ctx.arc(x, y - 6, size, Math.PI * 0.2, Math.PI * 0.8, false);
    ctx.stroke();
  }

  drawThinkingEye(ctx, x, y, radius, angle) {
    // Outer rotating orbital arc
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(x, y, radius, angle, angle + Math.PI * 1.2);
    ctx.stroke();

    // Center pupil
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  roundRect(ctx, x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
}

