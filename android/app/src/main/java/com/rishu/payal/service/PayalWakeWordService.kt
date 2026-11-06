package com.rishu.payal.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import com.rishu.payal.PayalApp
import com.rishu.payal.R
import com.rishu.payal.hud.PayalHudActivity
import kotlinx.coroutines.*
import kotlin.math.sqrt

class PayalWakeWordService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private var isListening = false
    private var audioRecord: AudioRecord? = null

    companion object {
        const val NOTIFICATION_ID = 1001
        const val SAMPLE_RATE = 16000
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startForegroundServiceNotification()
        startWakeWordDetection()
    }

    private fun startForegroundServiceNotification() {
        val launchIntent = Intent(this, PayalHudActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification: Notification = NotificationCompat.Builder(this, PayalApp.CHANNEL_ID)
            .setContentTitle("Payal Voice Assistant")
            .setContentText("Say \"Payal\" or tap to interact")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun startWakeWordDetection() {
        isListening = true
        serviceScope.launch {
            val minBuf = AudioRecord.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            val bufferSize = minBuf.coerceAtLeast(SAMPLE_RATE / 10) // 100ms buffer

            try {
                audioRecord = AudioRecord(
                    MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    bufferSize
                )

                if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                    return@launch
                }

                audioRecord?.startRecording()
                val buffer = ShortArray(bufferSize)

                var speechConsecutiveFrames = 0
                val thresholdRms = 1800.0 // Acoustic energy threshold

                while (isListening && isActive) {
                    val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                    if (read > 0) {
                        var sum = 0.0
                        for (i in 0 until read) {
                            sum += buffer[i] * buffer[i]
                        }
                        val rms = sqrt(sum / read)

                        if (rms > thresholdRms) {
                            speechConsecutiveFrames++
                            // When sustained voice is detected, trigger HUD
                            if (speechConsecutiveFrames >= 3) {
                                speechConsecutiveFrames = 0
                                triggerWakeActivation()
                                delay(3000) // Debounce triggers
                            }
                        } else {
                            if (speechConsecutiveFrames > 0) speechConsecutiveFrames--
                        }
                    }
                    delay(30)
                }
            } catch (_: SecurityException) {
                // Mic permission missing
            } catch (_: Exception) {
                // Audio device busy or interrupted
            }
        }
    }

    private fun triggerWakeActivation() {
        // Wake the screen if sleeping
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        val wakeLock = powerManager.newWakeLock(
            PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "payal:assistant_wake"
        )
        wakeLock.acquire(4000)

        // Launch HUD over lockscreen with auto-listen flag
        val hudIntent = Intent(this, PayalHudActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            putExtra("EXTRA_AUTO_LISTEN", true)
        }
        startActivity(hudIntent)
    }

    override fun onDestroy() {
        super.onDestroy()
        isListening = false
        serviceScope.cancel()
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (_: Exception) {}
        audioRecord = null
    }
}

