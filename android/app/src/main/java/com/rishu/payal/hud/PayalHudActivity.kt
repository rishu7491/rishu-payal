package com.rishu.payal.hud

import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageButton
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.rishu.payal.MainActivity
import com.rishu.payal.R
import com.rishu.payal.network.PayalApiClient
import com.rishu.payal.service.PayalOverlayService
import com.rishu.payal.voice.SpeechManager
import kotlinx.coroutines.launch

class PayalHudActivity : AppCompatActivity() {

    private lateinit var orbView: OrbView
    private lateinit var tvStateLabel: TextView
    private lateinit var tvSubtitles: TextView
    private lateinit var btnTalk: Button
    private lateinit var btnClose: ImageButton
    private lateinit var btnMinimize: ImageButton
    private lateinit var btnOpenWorkspace: Button

    private lateinit var speechManager: SpeechManager
    private val apiClient = PayalApiClient.getInstance()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupLockscreenFlags()
        setContentView(R.layout.activity_payal_hud)

        orbView = findViewById(R.id.orbView)
        tvStateLabel = findViewById(R.id.tvStateLabel)
        tvSubtitles = findViewById(R.id.tvSubtitles)
        btnTalk = findViewById(R.id.btnTalk)
        btnClose = findViewById(R.id.btnClose)
        btnMinimize = findViewById(R.id.btnMinimize)
        btnOpenWorkspace = findViewById(R.id.btnOpenWorkspace)

        initSpeech()
        initListeners()

        // If launched via wake-word, automatically start listening
        val autoListen = intent.getBooleanExtra("EXTRA_AUTO_LISTEN", false)
        if (autoListen) {
            startListeningSequence()
        }
    }

    private fun setupLockscreenFlags() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            val keyguardManager = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
            keyguardManager.requestDismissKeyguard(this, null)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }
    }

    private fun initSpeech() {
        speechManager = SpeechManager(
            context = this,
            onTranscript = { transcript ->
                handleTranscript(transcript)
            },
            onAmplitude = { amp ->
                orbView.audioAmplitude = amp
            },
            onSpeakingStarted = { text ->
                runOnUiThread {
                    orbView.currentState = OrbView.State.SPEAKING
                    tvStateLabel.text = "Responding to you..."
                    tvSubtitles.text = "\"$text\""
                }
            },
            onSpeakingEnded = {
                runOnUiThread {
                    orbView.currentState = OrbView.State.IDLE
                    tvStateLabel.text = "Tap or say \"Payal\""
                }
            },
            onError = { err ->
                runOnUiThread {
                    orbView.currentState = OrbView.State.IDLE
                    tvStateLabel.text = "Ready (Tap to speak)"
                }
            }
        )
    }

    private fun initListeners() {
        btnTalk.setOnClickListener {
            startListeningSequence()
        }

        orbView.setOnClickListener {
            startListeningSequence()
        }

        btnClose.setOnClickListener {
            finish()
        }

        btnMinimize.setOnClickListener {
            startService(Intent(this, PayalOverlayService::class.java))
            finish()
        }

        btnOpenWorkspace.setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }
    }

    private fun startListeningSequence() {
        orbView.currentState = OrbView.State.LISTENING
        tvStateLabel.text = "Listening to you..."
        tvSubtitles.text = "\"Listening...\""
        speechManager.startListening()
    }

    private fun handleTranscript(userQuery: String) {
        orbView.currentState = OrbView.State.THINKING
        tvStateLabel.text = "Thinking..."
        tvSubtitles.text = "\"Processing: $userQuery\""

        lifecycleScope.launch {
            val responseText = apiClient.sendChatMessage(userQuery)
            speechManager.speak(responseText)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        speechManager.destroy()
    }
}

