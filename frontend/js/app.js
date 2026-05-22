// ============================================================
// NEXUS INTERVIEW — Frontend Application
// Handles all UI interactions and API communication
// ============================================================


// ---------------------------
// State
// ---------------------------

const state = {
    sessionId: null,
    turnCount: 0,
    maxTurns: 10,
    difficulty: 'beginner',
    isStreaming: false,
    isActive: false
}


// ---------------------------
// DOM References
// ---------------------------

const dom = {
    bootScreen:       document.getElementById('boot-screen'),
    bootStatus:       document.getElementById('boot-status'),
    app:              document.getElementById('app'),
    chatWindow:       document.getElementById('chat-window'),
    chatPlaceholder:  document.getElementById('chat-placeholder'),
    userInput:        document.getElementById('user-input'),
    sendBtn:          document.getElementById('send-btn'),
    hintBtn:          document.getElementById('hint-btn'),
    scoreBtn:         document.getElementById('score-btn'),
    startBtn:         document.getElementById('start-btn'),
    topicInput:       document.getElementById('topic-input'),
    diffBtns:         document.querySelectorAll('.diff-btn'),
    turnCount:        document.getElementById('turn-count'),
    headerTopic:      document.getElementById('header-topic'),
    statusDot:        document.getElementById('status-dot'),
    scorePanel:       document.getElementById('score-panel'),
    restartBtn:       document.getElementById('restart-btn'),

    // Intel feed
    intelStatus:      document.getElementById('intel-status'),
    intelDifficulty:  document.getElementById('intel-difficulty'),
    intelTopic:       document.getElementById('intel-topic'),
    intelSession:     document.getElementById('intel-session'),
    intelTurns:       document.getElementById('intel-turns'),

    // Score fields
    scoreScalability:   document.getElementById('score-scalability'),
    scoreReliability:   document.getElementById('score-reliability'),
    scoreCommunication: document.getElementById('score-communication'),
    scoreOverall:       document.getElementById('score-overall'),
    scoreFeedback:      document.getElementById('score-feedback'),
    scoreStrengths:     document.getElementById('score-strengths'),
    scoreImprovements:  document.getElementById('score-improvements'),
}


// ---------------------------
// Boot Sequence
// ---------------------------

const bootMessages = [
    'INITIALIZING SYSTEMS...',
    'LOADING CLAUDE ENGINE...',
    'CALIBRATING INTERVIEWER...',
    'NEXUS ONLINE.'
]

function runBootSequence() {
    let i = 0
    const interval = setInterval(() => {
        if (i < bootMessages.length) {
            dom.bootStatus.textContent = bootMessages[i]
            i++
        } else {
            clearInterval(interval)
            setTimeout(() => {
                dom.bootScreen.style.opacity = '0'
                setTimeout(() => {
                    dom.bootScreen.style.display = 'none'
                    dom.app.classList.remove('hidden')
                }, 800)
            }, 400)
        }
    }, 550)
}


// ---------------------------
// Difficulty Selection
// ---------------------------

dom.diffBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        dom.diffBtns.forEach(b => b.classList.remove('active'))
        btn.classList.add('active')
        state.difficulty = btn.dataset.level
    })
})


// ---------------------------
// Start Interview
// ---------------------------

dom.startBtn.addEventListener('click', async () => {
    const topic = dom.topicInput.value.trim() || null

    dom.startBtn.disabled = true
    dom.startBtn.querySelector('.start-btn-text').textContent = 'CONNECTING...'

    try {
        const res = await fetch('/api/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                difficulty: state.difficulty,
                topic: topic
            })
        })

        if (!res.ok) throw new Error('Failed to start interview')

        const data = await res.json()

        // Update state
        state.sessionId  = data.session_id
        state.turnCount  = data.turn_count
        state.maxTurns   = data.max_turns
        state.isActive   = true

        // Update UI
        dom.chatPlaceholder.style.display = 'none'
        dom.userInput.disabled  = false
        dom.sendBtn.disabled    = false
        dom.hintBtn.disabled    = false
        dom.scoreBtn.disabled   = false
        dom.statusDot.classList.add('active')
        dom.startBtn.querySelector('.start-btn-text').textContent = 'SESSION ACTIVE'

        // Update intel feed
        updateIntel(data)

        // Render opening message
        appendMessage('nexus', data.message)

    } catch (err) {
        console.error(err)
        dom.startBtn.disabled = false
        dom.startBtn.querySelector('.start-btn-text').textContent = 'INITIATE SESSION'
        appendSystemMessage('❌ Failed to connect. Check your API key and try again.')
    }
})


// ---------------------------
// Send Message — Streaming
// ---------------------------

async function sendMessage() {
    const text = dom.userInput.value.trim()
    if (!text || state.isStreaming || !state.sessionId) return

    // Render user message
    appendMessage('user', text)
    dom.userInput.value = ''
    setInputLocked(true)

    // Create nexus bubble for streaming
    const { bubble } = appendMessage('nexus', '')
    bubble.classList.add('streaming')

    try {
        const res = await fetch('/api/interview/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                message: text
            })
        })

        if (!res.ok) throw new Error('Chat request failed')

        // Stream response
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let fullText = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value)
            fullText += chunk
            bubble.textContent = fullText
            scrollToBottom()
        }

        bubble.classList.remove('streaming')

        // Increment turn
        state.turnCount++
        updateTurnDisplay()

        // Check if max turns reached
        if (state.turnCount >= state.maxTurns) {
            appendSystemMessage(
                '⏱ Session complete. Click SCORE ME to receive your evaluation.'
            )
            setInputLocked(true)
            dom.scoreBtn.disabled = false
        }

    } catch (err) {
        console.error(err)
        bubble.textContent = '⚠ Connection interrupted. Please try again.'
        bubble.classList.remove('streaming')
    }

    setInputLocked(false)
}


// ---------------------------
// Get Hint
// ---------------------------

dom.hintBtn.addEventListener('click', async () => {
    if (!state.sessionId) return

    dom.hintBtn.disabled = true
    dom.hintBtn.textContent = '...'

    try {
        const res = await fetch('/api/interview/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId })
        })

        const data = await res.json()
        appendHint(data.hint)

    } catch (err) {
        appendSystemMessage('❌ Could not retrieve hint.')
    }

    dom.hintBtn.disabled = false
    dom.hintBtn.textContent = 'HINT'
})


// ---------------------------
// Score Interview
// ---------------------------

dom.scoreBtn.addEventListener('click', async () => {
    if (!state.sessionId) return

    dom.scoreBtn.disabled = true
    dom.scoreBtn.textContent = 'SCORING...'

    appendSystemMessage('⚙ Nexus is reviewing your performance...')

    try {
        const res = await fetch('/api/interview/score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId })
        })

        const data = await res.json()
        renderScore(data)
        state.isActive = false
        dom.statusDot.classList.remove('active')
        setInputLocked(true)

    } catch (err) {
        appendSystemMessage('❌ Scoring failed. Please try again.')
        dom.scoreBtn.disabled = false
        dom.scoreBtn.textContent = 'SCORE ME'
    }
})


// ---------------------------
// Restart Session
// ---------------------------

dom.restartBtn.addEventListener('click', () => {
    // Reset state
    state.sessionId  = null
    state.turnCount  = 0
    state.isActive   = false
    state.isStreaming = false

    // Reset UI
    dom.chatWindow.innerHTML = ''
    dom.chatWindow.appendChild(createPlaceholder())
    dom.userInput.value    = ''
    dom.userInput.disabled = true
    dom.sendBtn.disabled   = true
    dom.hintBtn.disabled   = true
    dom.scoreBtn.disabled  = true
    dom.scoreBtn.textContent = 'SCORE ME'
    dom.statusDot.classList.remove('active')
    dom.scorePanel.classList.add('hidden')
    dom.startBtn.disabled = false
    dom.startBtn.querySelector('.start-btn-text').textContent = 'INITIATE SESSION'
    dom.headerTopic.textContent = '—'
    dom.topicInput.value = ''

    // Reset intel
    dom.intelStatus.textContent     = 'OFFLINE'
    dom.intelDifficulty.textContent = '—'
    dom.intelTopic.textContent      = '—'
    dom.intelSession.textContent    = '—'
    dom.intelTurns.textContent      = '0 / 10'
    dom.turnCount.textContent       = '0/10'
})


// ---------------------------
// Send on Enter (Shift+Enter for newline)
// ---------------------------

dom.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
    }
})

dom.sendBtn.addEventListener('click', sendMessage)


// ---------------------------
// UI Helpers
// ---------------------------

function appendMessage(role, text) {
    const wrap = document.createElement('div')
    wrap.className = `message ${role}`

    const label = document.createElement('div')
    label.className = 'message-label'
    label.textContent = role === 'nexus' ? 'NEXUS' : 'YOU'

    const bubble = document.createElement('div')
    bubble.className = 'message-bubble'
    bubble.textContent = text

    wrap.appendChild(label)
    wrap.appendChild(bubble)
    dom.chatWindow.appendChild(wrap)
    scrollToBottom()

    return { wrap, bubble }
}

function appendHint(text) {
    const div = document.createElement('div')
    div.className = 'hint-bubble'
    div.textContent = `💡 ${text}`
    dom.chatWindow.appendChild(div)
    scrollToBottom()
}

function appendSystemMessage(text) {
    const div = document.createElement('div')
    div.style.cssText = `
        text-align: center;
        font-size: 0.65rem;
        letter-spacing: 0.15em;
        color: var(--text-muted);
        padding: 0.5rem;
    `
    div.textContent = text
    dom.chatWindow.appendChild(div)
    scrollToBottom()
}

function createPlaceholder() {
    const div = document.createElement('div')
    div.className = 'chat-placeholder'
    div.id = 'chat-placeholder'
    div.innerHTML = `
        <div class="placeholder-icon">⬡</div>
        <div class="placeholder-text">
            Configure your session and hit<br/>
            <strong>INITIATE SESSION</strong> to begin.
        </div>
    `
    return div
}

function scrollToBottom() {
    dom.chatWindow.scrollTop = dom.chatWindow.scrollHeight
}

function setInputLocked(locked) {
    state.isStreaming      = locked
    dom.userInput.disabled = locked
    dom.sendBtn.disabled   = locked
    dom.hintBtn.disabled   = locked
}

function updateTurnDisplay() {
    const display = `${state.turnCount}/${state.maxTurns}`
    dom.turnCount.textContent      = display
    dom.intelTurns.textContent     = `${state.turnCount} / ${state.maxTurns}`
}

function updateIntel(data) {
    dom.headerTopic.textContent     = data.question_topic.toUpperCase()
    dom.intelStatus.textContent     = 'ACTIVE'
    dom.intelDifficulty.textContent = data.difficulty.toUpperCase()
    dom.intelTopic.textContent      = data.question_topic
    dom.intelSession.textContent    = data.session_id.split('-')[0].toUpperCase()
    dom.intelTurns.textContent      = `0 / ${data.max_turns}`
}

function renderScore(data) {
    dom.scorePanel.classList.remove('hidden')

    dom.scoreScalability.textContent   = `${data.score.scalability}/10`
    dom.scoreReliability.textContent   = `${data.score.reliability}/10`
    dom.scoreCommunication.textContent = `${data.score.communication}/10`
    dom.scoreOverall.textContent       = `${data.score.overall}/10`
    dom.scoreFeedback.textContent      = data.feedback

    // Strengths
    dom.scoreStrengths.innerHTML = data.strengths
        .map(s => `<div class="score-tag">✓ ${s}</div>`)
        .join('')

    // Improvements
    dom.scoreImprovements.innerHTML = data.improvements
        .map(i => `<div class="score-tag">↑ ${i}</div>`)
        .join('')

    // Scroll score panel into view
    dom.scorePanel.scrollIntoView({ behavior: 'smooth' })
}


// ---------------------------
// Boot
// ---------------------------

runBootSequence()