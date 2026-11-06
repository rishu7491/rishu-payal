package com.rishu.payal

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build

class PayalApp : Application() {

    companion object {
        const val CHANNEL_ID = "payal_assistant_channel"
        const val CHANNEL_NAME = "Payal Assistant Service"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Foreground service notification for Payal always-available assistant"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }
}

