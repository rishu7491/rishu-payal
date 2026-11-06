package com.rishu.payal.voice

import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import com.rishu.payal.network.PayalApiClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.net.URLEncoder
import java.util.Locale

class SpeechManager(
    private val context: Context,
    private val onTranscript: (String) -> Unit,
    private val onAmplitude: (Float) -> Unit,
    private val onSpeakingStarted: (String) -> Unit,
    private val onSpeakingEnded: () -> Unit,
    private val onError: (String) -> Unit
) : TextToSpeech.OnInitListener {

    private var speechRecognizer: SpeechRecognizer? = null
    private var tts: TextToSpeech? = null
    private var isTtsReady = false
    private var mediaPlayer: MediaPlayer? = null
    private var visualizerJob: Job? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.Main)
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    init {
        tts = TextToSpeech(context.applicationContext, this)
        initRecognizer()
    }

    private fun initRecognizer() {
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
                setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {}
                    override fun onBeginningOfSpeech() {}
                    override fun onRmsChanged(rmsdB: Float) {
                        val norm = ((rmsdB + 2f) / 12f).coerceIn(0.0f, 1.0f)
                        onAmplitude(norm)
                    }
                    override fun onBufferReceived(buffer: ByteArray?) {}
                    override fun onEndOfSpeech() {
                        onAmplitude(0.0f)
                    }
                    override fun onError(error: Int) {
                        onAmplitude(0.0f)
                        onError("Recognition code: $error")
                    }
                    override fun onResults(results: Bundle?) {
                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        val text = matches?.firstOrNull() ?: ""
                        if (text.isNotBlank()) {
                            onTranscript(text)
                        } else {
                            onError("No speech detected")
                        }
                    }
                    override fun onPartialResults(partialResults: Bundle?) {}
                    override fun onEvent(eventType: Int, params: Bundle?) {}
                })
            }
        }
    }

    fun startListening() {
        requestAudioFocus()
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "hi-IN")
            putExtra(RecognizerIntent.EXTRA_SUPPORTED_LANGUAGES, arrayListOf("hi-IN", "en-US", "en-IN"))
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }
        speechRecognizer?.startListening(intent)
    }

    fun stopListening() {
        speechRecognizer?.stopListening()
        abandonAudioFocus()
    }

    fun cleanTextForSpeech(raw: String): String {
        return raw.replace(Regex("```[\\s\\S]*?```"), "Code ready hai.")
            .replace(Regex("https?://\\S+"), "")
            .replace(Regex("[*#`_~|\\[\\]()<>{}]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
    }

    fun speak(text: String) {
        val clean = cleanTextForSpeech(text)
        if (clean.isBlank()) return

        stopSpeaking()
        requestAudioFocus()
        onSpeakingStarted(clean)

        // Try streaming Ultra-Natural Neural TTS from Payal Core server
        scope.launch(Dispatchers.IO) {
            val baseUrl = PayalApiClient.getInstance().getActiveBaseUrl()
            val encoded = try { URLEncoder.encode(clean, "UTF-8") } catch (_: Exception) { clean }
            val ttsUrl = "$baseUrl/api/multimodal/tts?text=$encoded"

            try {
                val mp = MediaPlayer().apply {
                    setAudioAttributes(
                        AudioAttributes.Builder()
                            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                            .setUsage(AudioAttributes.USAGE_ASSISTANT)
                            .build()
                    )
                    setDataSource(ttsUrl)
                    setOnPreparedListener { player ->
                        player.start()
                        startAmplitudeVisualizer()
                    }
                    setOnCompletionListener {
                        stopSpeaking()
                    }
                    setOnErrorListener { _, _, _ ->
                        mainHandler.post {
                            fallbackLocalTts(clean)
                        }
                        true
                    }
                    prepareAsync()
                }
                mediaPlayer = mp
            } catch (e: Exception) {
                mainHandler.post {
                    fallbackLocalTts(clean)
                }
            }
        }
    }

    private fun startAmplitudeVisualizer() {
        visualizerJob?.cancel()
        visualizerJob = scope.launch {
            var step = 0.0
            while (isActive && mediaPlayer?.isPlaying == true) {
                step += 0.25
                val fakeRms = 0.45f + (Math.sin(step) * 0.35f).toFloat()
                onAmplitude(fakeRms.coerceIn(0.1f, 1.0f))
                delay(60)
            }
            onAmplitude(0.0f)
        }
    }

    private fun fallbackLocalTts(cleanText: String) {
        if (!isTtsReady || tts == null) {
            onSpeakingEnded()
            abandonAudioFocus()
            return
        }

        val params = Bundle().apply {
            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, "payal_${System.currentTimeMillis()}")
        }
        tts?.speak(cleanText, TextToSpeech.QUEUE_FLUSH, params, "payal_reply_id")
    }

    fun stopSpeaking() {
        visualizerJob?.cancel()
        visualizerJob = null
        try {
            mediaPlayer?.stop()
            mediaPlayer?.release()
        } catch (_: Exception) {}
        mediaPlayer = null

        tts?.stop()
        abandonAudioFocus()
        onAmplitude(0.0f)
        onSpeakingEnded()
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            val hiLocale = Locale("hi", "IN")
            val enLocale = Locale("en", "IN")

            // Look for Google Neural Hindi Voice
            try {
                val voices = tts?.voices
                if (voices != null) {
                    val bestVoice = voices.find { v ->
                        val n = v.name.lowercase(Locale.ROOT)
                        val l = v.locale.language
                        (l == "hi" || l == "hin") && (n.contains("hie") || n.contains("neural") || n.contains("google"))
                    } ?: voices.find { it.locale.language == "hi" }
                    if (bestVoice != null) {
                        tts?.voice = bestVoice
                    } else {
                        tts?.language = hiLocale
                    }
                } else {
                    tts?.language = hiLocale
                }
            } catch (_: Exception) {
                tts?.language = hiLocale
            }

            tts?.setPitch(1.02f)
            tts?.setSpeechRate(1.02f)

            tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    startAmplitudeVisualizer()
                }
                override fun onDone(utteranceId: String?) {
                    mainHandler.post {
                        stopSpeaking()
                    }
                }
                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) {
                    mainHandler.post {
                        stopSpeaking()
                    }
                }
            })
        }
    }

    private fun requestAudioFocus() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val req = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANT)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                )
                .build()
            audioManager.requestAudioFocus(req)
        } else {
            @Suppress("DEPRECATION")
            audioManager.requestAudioFocus(
                null,
                AudioManager.STREAM_VOICE_CALL,
                AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK
            )
        }
    }

    private fun abandonAudioFocus() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val req = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK).build()
            audioManager.abandonAudioFocusRequest(req)
        } else {
            @Suppress("DEPRECATION")
            audioManager.abandonAudioFocus(null)
        }
    }

    fun destroy() {
        speechRecognizer?.destroy()
        stopSpeaking()
        tts?.shutdown()
    }
}
