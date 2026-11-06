package com.rishu.payal.hud

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import android.view.animation.LinearInterpolator
import kotlin.math.*

/**
 * High-performance hardware-accelerated Holographic Energy Orb for Payal Assistant.
 * Renders 5 reactive visual states: IDLE, LISTENING, THINKING, SPEAKING, ERROR.
 */
class OrbView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    enum class State {
        IDLE,
        LISTENING,
        THINKING,
        SPEAKING,
        ERROR
    }

    var currentState: State = State.IDLE
        set(value) {
            if (field != value) {
                field = value
                stateStartTime = System.currentTimeMillis()
                invalidate()
            }
        }

    // Audio amplitude factor (0.0 to 1.0) for reactive waveforms
    var audioAmplitude: Float = 0.0f
        set(value) {
            field = value.coerceIn(0.0f, 1.0f)
            invalidate()
        }

    private var stateStartTime = System.currentTimeMillis()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
    }
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#F0F4F8")
        textAlign = Paint.Align.CENTER
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
    }

    // Color Palette
    private val colCyan = Color.parseColor("#00F5D4")
    private val colElectricBlue = Color.parseColor("#00B4D8")
    private val colPurple = Color.parseColor("#7B2CBF")
    private val colMagenta = Color.parseColor("#C77DFF")
    private val colCrimson = Color.parseColor("#FF2448")
    private val colAmber = Color.parseColor("#FFB703")

    private fun withAlpha(color: Int, alpha: Int): Int {
        return (color and 0x00FFFFFF) or ((alpha and 0xFF) shl 24)
    }

    // Particle system
    private data class Particle(
        var x: Float,
        var y: Float,
        var radius: Float,
        var angle: Float,
        var speed: Float,
        var alpha: Int,
        var color: Int
    )

    private val particles = ArrayList<Particle>()
    private val numParticles = 36

    init {
        for (i in 0 until numParticles) {
            particles.add(
                Particle(
                    x = 0f,
                    y = 0f,
                    radius = (2f + (i % 4) * 1.5f),
                    angle = (i * (360f / numParticles)),
                    speed = (0.5f + (i % 3) * 0.4f),
                    alpha = 150 + (i % 100),
                    color = if (i % 2 == 0) colCyan else colMagenta
                )
            )
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0 || h <= 0) return

        val cx = w / 2f
        val cy = h / 2f
        val baseRadius = min(w, h) * 0.28f
        val time = (System.currentTimeMillis() - stateStartTime) / 1000f

        when (currentState) {
            State.IDLE -> drawIdleState(canvas, cx, cy, baseRadius, time)
            State.LISTENING -> drawListeningState(canvas, cx, cy, baseRadius, time)
            State.THINKING -> drawThinkingState(canvas, cx, cy, baseRadius, time)
            State.SPEAKING -> drawSpeakingState(canvas, cx, cy, baseRadius, time)
            State.ERROR -> drawErrorState(canvas, cx, cy, baseRadius, time)
        }

        // Keep 60fps loop active for continuous organic animations
        postInvalidateOnAnimation()
    }

    /**
     * IDLE STATE: Calm glowing holographic ring with subtle breathing pulse and floating energy particles.
     */
    private fun drawIdleState(canvas: Canvas, cx: Float, cy: Float, r: Float, t: Float) {
        val pulse = sin(t * 2.0f) * 6f
        val currentR = r + pulse

        // Outer glow aura
        paint.style = Paint.Style.FILL
        val glowShader = RadialGradient(
            cx, cy, currentR * 1.4f,
            intArrayOf(withAlpha(colPurple, 0x66), withAlpha(colElectricBlue, 0x22), Color.TRANSPARENT),
            floatArrayOf(0.0f, 0.7f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = glowShader
        canvas.drawCircle(cx, cy, currentR * 1.4f, paint)
        paint.shader = null

        // Inner glowing core
        val coreShader = RadialGradient(
            cx, cy, currentR,
            intArrayOf(withAlpha(colCyan, 0x99), withAlpha(colPurple, 0x88), Color.TRANSPARENT),
            floatArrayOf(0.0f, 0.8f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = coreShader
        canvas.drawCircle(cx, cy, currentR, paint)
        paint.shader = null

        // Neon ring boundary
        strokePaint.strokeWidth = 3f
        strokePaint.color = colCyan
        strokePaint.alpha = (180 + (sin(t * 3f) * 40)).toInt().coerceIn(0, 255)
        canvas.drawCircle(cx, cy, currentR, strokePaint)

        // Subtle orbiting particles
        drawParticles(canvas, cx, cy, currentR * 0.9f, t * 20f)

        // Central branding: PAYAL
        textPaint.textSize = r * 0.32f
        textPaint.color = Color.WHITE
        textPaint.alpha = 240
        canvas.drawText("PAYAL", cx, cy + (textPaint.textSize * 0.35f), textPaint)
    }

    /**
     * LISTENING STATE: Audio-reactive concentric acoustic ripples + glowing microphone core.
     */
    private fun drawListeningState(canvas: Canvas, cx: Float, cy: Float, r: Float, t: Float) {
        val reactR = r * (1.0f + audioAmplitude * 0.35f)

        // Multiple expanding acoustic ripples
        for (i in 1..3) {
            val rippleOffset = ((t * 1.2f + i * 0.33f) % 1.0f)
            val rippleRadius = r + rippleOffset * (r * 0.8f)
            val rippleAlpha = ((1.0f - rippleOffset) * 160).toInt().coerceIn(0, 255)

            strokePaint.strokeWidth = 3f + (audioAmplitude * 4f)
            strokePaint.color = colCyan
            strokePaint.alpha = rippleAlpha
            canvas.drawCircle(cx, cy, rippleRadius, strokePaint)
        }

        // Bright active core
        paint.style = Paint.Style.FILL
        val activeShader = RadialGradient(
            cx, cy, reactR,
            intArrayOf(colCyan, withAlpha(colElectricBlue, 0xCC), withAlpha(colPurple, 0x44)),
            floatArrayOf(0.0f, 0.6f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = activeShader
        canvas.drawCircle(cx, cy, reactR, paint)
        paint.shader = null

        // Draw Stylized Microphone Glyph
        drawMicrophoneIcon(canvas, cx, cy, r * 0.45f)
    }

    /**
     * THINKING STATE: Multi-layered gyroscopic 3D orbital rings spinning with plasma sparks.
     */
    private fun drawThinkingState(canvas: Canvas, cx: Float, cy: Float, r: Float, t: Float) {
        // Core pulsating atomic sphere
        val corePulse = (sin(t * 5f) * 4f)
        paint.style = Paint.Style.FILL
        val thinkShader = RadialGradient(
            cx, cy, r * 0.5f + corePulse,
            intArrayOf(colMagenta, colPurple, Color.TRANSPARENT),
            floatArrayOf(0.0f, 0.7f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = thinkShader
        canvas.drawCircle(cx, cy, r * 0.5f + corePulse, paint)
        paint.shader = null

        // 3 Layered Gyroscopic Elliptical Orbits (Angled at 0°, 60°, 120°)
        val angles = floatArrayOf(0f, 60f, 120f)
        val speeds = floatArrayOf(90f, -120f, 75f)

        for (i in angles.indices) {
            canvas.save()
            canvas.rotate(angles[i] + t * speeds[i], cx, cy)

            strokePaint.strokeWidth = 3.5f
            strokePaint.color = if (i % 2 == 0) colCyan else colMagenta
            strokePaint.alpha = 210

            val oval = RectF(cx - r * 1.15f, cy - r * 0.45f, cx + r * 1.15f, cy + r * 0.45f)
            canvas.drawOval(oval, strokePaint)

            // Orbiting plasma bead on each ring
            val beadAngle = (t * 4f * (i + 1))
            val beadX = cx + (r * 1.15f) * cos(beadAngle).toFloat()
            val beadY = cy + (r * 0.45f) * sin(beadAngle).toFloat()

            paint.style = Paint.Style.FILL
            paint.color = Color.WHITE
            canvas.drawCircle(beadX, beadY, 5f, paint)

            canvas.restore()
        }

        // Floating dynamic sparks
        drawParticles(canvas, cx, cy, r * 1.2f, t * 45f)
    }

    /**
     * SPEAKING STATE: Organic turbulent plasma corona / energy fire ring reacting to speech.
     */
    private fun drawSpeakingState(canvas: Canvas, cx: Float, cy: Float, r: Float, t: Float) {
        val voiceBoost = audioAmplitude * 20f

        // Plasma Corona with wavy spikes
        val path = Path()
        val segments = 48
        val angleStep = (2 * PI / segments).toFloat()

        for (i in 0 until segments) {
            val angle = i * angleStep
            val wave = sin(angle * 6f + t * 8f) * (6f + voiceBoost) + cos(angle * 3f - t * 5f) * 4f
            val curR = r + wave
            val px = cx + curR * cos(angle)
            val py = cy + curR * sin(angle)

            if (i == 0) {
                path.moveTo(px, py)
            } else {
                path.lineTo(px, py)
            }
        }
        path.close()

        // Corona fill
        paint.style = Paint.Style.FILL
        val speakShader = RadialGradient(
            cx, cy, r * 1.3f,
            intArrayOf(withAlpha(colCyan, 0xCC), withAlpha(colPurple, 0x99), withAlpha(colMagenta, 0x33)),
            floatArrayOf(0.0f, 0.6f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = speakShader
        canvas.drawPath(path, paint)
        paint.shader = null

        // Corona outline glow
        strokePaint.strokeWidth = 4f
        strokePaint.color = colCyan
        strokePaint.alpha = 240
        canvas.drawPath(path, strokePaint)

        // Subtitle indicator waves
        drawSpeechWaveform(canvas, cx, cy + r * 1.35f, r * 1.2f, t)
    }

    /**
     * ERROR STATE: Amber / crimson warning pulse.
     */
    private fun drawErrorState(canvas: Canvas, cx: Float, cy: Float, r: Float, t: Float) {
        val pulse = (sin(t * 6f) * 5f)
        paint.style = Paint.Style.FILL
        val errShader = RadialGradient(
            cx, cy, r + pulse,
            intArrayOf(colAmber, colCrimson, Color.TRANSPARENT),
            floatArrayOf(0.0f, 0.7f, 1.0f),
            Shader.TileMode.CLAMP
        )
        paint.shader = errShader
        canvas.drawCircle(cx, cy, r + pulse, paint)
        paint.shader = null

        strokePaint.strokeWidth = 4f
        strokePaint.color = colCrimson
        strokePaint.alpha = 230
        canvas.drawCircle(cx, cy, r + pulse, strokePaint)

        textPaint.textSize = r * 0.45f
        textPaint.color = Color.WHITE
        canvas.drawText("!", cx, cy + (textPaint.textSize * 0.35f), textPaint)
    }

    private fun drawParticles(canvas: Canvas, cx: Float, cy: Float, maxR: Float, rotationDeg: Float) {
        paint.style = Paint.Style.FILL
        for (p in particles) {
            val rad = Math.toRadians((p.angle + rotationDeg).toDouble())
            val px = cx + (maxR * 0.75f + (sin(p.angle) * 15f)) * cos(rad).toFloat()
            val py = cy + (maxR * 0.75f + (cos(p.angle) * 15f)) * sin(rad).toFloat()

            paint.color = p.color
            paint.alpha = p.alpha
            canvas.drawCircle(px, py, p.radius, paint)
        }
    }

    private fun drawMicrophoneIcon(canvas: Canvas, cx: Float, cy: Float, size: Float) {
        val micPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.STROKE
            strokeWidth = 4f
            strokeCap = Paint.Cap.ROUND
        }
        val micW = size * 0.35f
        val micH = size * 0.7f

        // Mic capsule
        val rect = RectF(cx - micW / 2f, cy - micH / 2f, cx + micW / 2f, cy + micH / 2f)
        canvas.drawRoundRect(rect, micW / 2f, micW / 2f, micPaint)

        // Mic U-cradle
        val cradleRect = RectF(cx - micW * 0.85f, cy - micH * 0.2f, cx + micW * 0.85f, cy + micH * 0.75f)
        canvas.drawArc(cradleRect, 0f, 180f, false, micPaint)

        // Mic base stand
        canvas.drawLine(cx, cy + micH * 0.75f, cx, cy + micH * 1.05f, micPaint)
        canvas.drawLine(cx - micW * 0.5f, cy + micH * 1.05f, cx + micW * 0.5f, cy + micH * 1.05f, micPaint)
    }

    private fun drawSpeechWaveform(canvas: Canvas, cx: Float, y: Float, width: Float, t: Float) {
        val bars = 16
        val barW = width / (bars * 2f)
        val startX = cx - width / 2f

        paint.style = Paint.Style.FILL
        paint.color = colCyan

        for (i in 0 until bars) {
            val barH = (sin(t * 10f + i * 0.6f) * 12f + (audioAmplitude * 20f)).coerceAtLeast(4f)
            val bx = startX + i * (barW * 2f)
            val rect = RectF(bx, y - barH, bx + barW, y + barH)
            paint.alpha = (140 + (sin(t * 8f + i) * 80)).toInt().coerceIn(50, 255)
            canvas.drawRoundRect(rect, barW / 2f, barW / 2f, paint)
        }
    }
}

