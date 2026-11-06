package com.rishu.payal

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.rishu.payal.hud.PayalHudActivity
import com.rishu.payal.network.PayalApiClient
import com.rishu.payal.service.PayalOverlayService
import com.rishu.payal.service.PayalWakeWordService
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var tvCoreStatusBadge: TextView
    private lateinit var btnLaunchHud: Button
    private lateinit var btnToggleVoiceService: Button
    private lateinit var btnToggleFloatingBubble: Button
    private lateinit var webViewWorkspace: WebView

    private val apiClient = PayalApiClient.getInstance()

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val recordAudioGranted = permissions[Manifest.permission.RECORD_AUDIO] ?: false
        if (recordAudioGranted) {
            startWakeWordService()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvCoreStatusBadge = findViewById(R.id.tvCoreStatusBadge)
        btnLaunchHud = findViewById(R.id.btnLaunchHud)
        btnToggleVoiceService = findViewById(R.id.btnToggleVoiceService)
        btnToggleFloatingBubble = findViewById(R.id.btnToggleFloatingBubble)
        webViewWorkspace = findViewById(R.id.webViewWorkspace)

        initWorkspaceWebView()
        initListeners()
        checkCoreHealth()
    }

    private fun initListeners() {
        btnLaunchHud.setOnClickListener {
            startActivity(Intent(this, PayalHudActivity::class.java))
        }

        btnToggleVoiceService.setOnClickListener {
            checkAndRequestAudioPermission()
        }

        btnToggleFloatingBubble.setOnClickListener {
            checkAndStartOverlay()
        }
    }

    private fun checkCoreHealth() {
        lifecycleScope.launch {
            val isOnline = apiClient.checkHealth()
            if (isOnline) {
                tvCoreStatusBadge.text = "Core: Online (Connected)"
                tvCoreStatusBadge.setTextColor(ContextCompat.getColor(this@MainActivity, R.color.status_green))
            } else {
                tvCoreStatusBadge.text = "Core: Offline (Local Mode)"
                tvCoreStatusBadge.setTextColor(ContextCompat.getColor(this@MainActivity, R.color.crimson_glow))
            }
        }
    }

    private fun checkAndRequestAudioPermission() {
        val permissions = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val allGranted = permissions.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }

        if (allGranted) {
            startWakeWordService()
        } else {
            requestPermissionLauncher.launch(permissions.toTypedArray())
        }
    }

    private fun startWakeWordService() {
        val serviceIntent = Intent(this, PayalWakeWordService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        btnToggleVoiceService.text = "Wake-Word: Active"
    }

    private fun checkAndStartOverlay() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(this)) {
                val intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                )
                startActivity(intent)
                return
            }
        }
        startService(Intent(this, PayalOverlayService::class.java))
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun initWorkspaceWebView() {
        webViewWorkspace.settings.javaScriptEnabled = true
        webViewWorkspace.settings.domStorageEnabled = true
        webViewWorkspace.webViewClient = WebViewClient()

        // Load reverse ADB port localhost with trailing slash
        webViewWorkspace.loadUrl("http://127.0.0.1:8000/app/")
    }
}

