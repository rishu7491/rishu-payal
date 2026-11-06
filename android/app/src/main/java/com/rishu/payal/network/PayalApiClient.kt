package com.rishu.payal.network

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class PayalApiClient {

    companion object {
        // Primary: reverse ADB localhost; Secondary: Local Wi-Fi Laptop IP
        private const val BASE_URL_USB = "http://127.0.0.1:8000"
        private const val BASE_URL_WIFI = "http://10.196.121.14:8000"

        @Volatile
        private var instance: PayalApiClient? = null

        fun getInstance(): PayalApiClient =
            instance ?: synchronized(this) {
                instance ?: PayalApiClient().also { instance = it }
            }
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private var activeBaseUrl: String = BASE_URL_USB

    /**
     * Checks if the laptop FastAPI server is accessible.
     */
    suspend fun checkHealth(): Boolean = withContext(Dispatchers.IO) {
        val candidates = listOf(
            BASE_URL_WIFI,
            BASE_URL_USB
        )
        for (url in candidates) {
            try {
                val request = Request.Builder()
                    .url("$url/api/v1/health")
                    .get()
                    .build()
                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        activeBaseUrl = url
                        return@withContext true
                    }
                }
            } catch (_: Exception) {
                // Try next candidate
            }
        }
        return@withContext false
    }

    /**
     * Sends voice or text message to Payal Core Engine and returns the clean conversational response.
     */
    suspend fun sendChatMessage(userText: String): String = withContext(Dispatchers.IO) {
        val isHealthy = checkHealth()
        if (!isHealthy) {
            return@withContext "Rishu, your laptop appears to be offline right now. I'm operating in phone-only mode."
        }

        try {
            val jsonBody = JSONObject().apply {
                put("message", userText)
                put("stream", false)
            }
            val body = jsonBody.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("$activeBaseUrl/api/v1/chat")
                .post(body)
                .build()

            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val jsonObj = JSONObject(respStr)
                    return@withContext jsonObj.optString("response", "All systems operational, Rishu.")
                } else {
                    return@withContext "I encountered a processing issue with the core engine (HTTP ${response.code})."
                }
            }
        } catch (e: Exception) {
            return@withContext "Unable to reach Payal core engine. Please check laptop connection."
        }
    }
}

