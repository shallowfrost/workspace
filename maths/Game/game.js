
function rand(a, b) {
    return Math.floor(Math.random() * (b - a + 1)) + a
}


function construct(chars) {
    const eq = [
        rand(0, 1),
        rand(-20, 20),
        rand(-20, 20),
        rand(-50, 50)
    ]
    const a = eq[0] === 0 ? eq[1] : eq[2]
    const b = eq[0] === 1 ? eq[1] : eq[2]
    const constructed = []
    constructed.push(a)
    constructed.push(chars[eq[0]])
    constructed.push(b < 0 ? " - " : " + ")
    constructed.push(Math.abs(b))
    constructed.push(chars[eq[0] === 0 ? 1 : 0])
    constructed.push(" = ")
    constructed.push(eq[3])
    return [eq, constructed]
}


function readable(eq) {
    let txt = ""
    for (let i = 0; i < eq.length; i++) {
        txt += eq[i]
    }

    return txt
}


function solve(eq1, eq2) {
    let a1 = eq1[1]
    let b1 = eq1[2]
    let c1 = eq1[3]
    let a2 = eq2[1]
    let b2 = eq2[2]
    let c2 = eq2[3]
    let det = a1 * b2 - a2 * b1
    let x = (c1 * b2 - c2 * b1) / det
    let y = (a1 * c2 - a2 * c1) / det
    return [x, y]
}


function getAnswers(x, y, count) {
    const answers = []
    for (let i = 0; i < count; i++) {
        answers.push(
            `(${(x + Math.random() * 40 - 20).toFixed(2)}
            
            , ${(y + Math.random() * 40 - 20).toFixed(2)}
            
            )`
        )
    }


    const correct = rand(0, count - 1)
    const correctAnswer = `(${x.toFixed(2)}
    
    , ${y.toFixed(2)}
    
    )`
    answers[correct] = correctAnswer
    const mistakes = [
        `(${y.toFixed(2)}
        
        , ${x.toFixed(2)}
        
        )`,
        `(${(-x).toFixed(2)}
        
        , ${y.toFixed(2)}
        
        )`,
        `(${x.toFixed(2)}
        
        , ${(-y).toFixed(2)}
        
        )`,
        `(${(x + 1).toFixed(2)}
        
        , ${(y - 1).toFixed(2)}
        
        )`
    ]
    let mistake = mistakes[rand(0, mistakes.length - 1)]
    if (mistake !== correctAnswer) {
        let slot
        do {
            slot = rand(0, count - 1)
        }
        
        while (slot === correct)
        answers[slot] = mistake
    }


    const used = new Set()
    for (let i = 0; i < answers.length; i++) {
        while (used.has(answers[i])) {
            answers[i] =
                `(${(x + Math.random() * 40 - 20).toFixed(2)}
                
                , ${(y + Math.random() * 40 - 20).toFixed(2)}
                
                )`
        }


        used.add(answers[i])
    }


    return [answers, correct]
}


let player = 1
let score1 = 0
let score2 = 0
let mode = "time"
let timer = 60
let timerInterval
let pointGoal = 10
let name1 = "Player 1"
let name2 = "Player 2"
function updateUI() {
    document.getElementById("p1").textContent = score1
    document.getElementById("p2").textContent = score2
    const turnName = player === 1 ? name1 : name2
    document.getElementById("turn").textContent = turnName
    if (mode === "time") {
        document.getElementById("timer").textContent = "Time: " + timer
    }
    
    else {
        document.getElementById("timer").textContent = "Goal: " + pointGoal
    }


}


function startGame(m) {
    mode = m
    score1 = 0
    score2 = 0
    player = 1
    name1 = document.getElementById("name1").value
    name2 = document.getElementById("name2").value
    document.getElementById("p1name").textContent = name1
    document.getElementById("p2name").textContent = name2
    timer = parseInt(document.getElementById("timeInput").value)
    pointGoal = parseInt(document.getElementById("pointInput").value)
    document.getElementById("modeSelect").style.display = "none"
    if (mode === "time") {
        timerInterval = setInterval(() => {
            timer--
            updateUI()
            if (timer <= 0) {
                clearInterval(timerInterval)
                endGame()
            }


        }
        
        , 1000)
    }


    updateUI()
    initGame()
}


function switchPlayer() {
    player = player === 1 ? 2 : 1
    updateUI()
}


function addPoint(correct) {
    if (player === 1) {
        score1 += correct ? 1 : -1
    }
    
    else {
        score2 += correct ? 1 : -1
    }


    if (mode === "points") {
        if (score1 >= pointGoal || score2 >= pointGoal) {
            endGame()
            return
        }


    }


    switchPlayer()
    setTimeout(initGame, 700)
}


function endGame() {
    let msg = ""
    if (score1 > score2) msg = name1 + " Wins!"
    else if (score2 > score1) msg = name2 + " Wins!"
    else msg = "Tie Game!"
    alert(msg)
    location.reload()
}


function initGame() {
    const [parts1, eq1] = construct(["x", "y"])
    const [parts2, eq2] = construct(["x", "y"])
    const tx1 = readable(eq1)
    const tx2 = readable(eq2)
    const [x, y] = solve(parts1, parts2)
    const [answers, correct] = getAnswers(x, y, 5)
    document.getElementById("eq1").textContent = tx1
    document.getElementById("eq2").textContent = tx2
    const choices = document.getElementById("choices")
    choices.innerHTML = ""
    answers.forEach((ans, i) => {
        const b = document.createElement("button")
        b.textContent = ans
        b.onclick = () => {
            if (i === correct) {
                b.style.background = "green"
                addPoint(true)

            }
            
            else {
                b.style.background = "red"
                addPoint(false)

            }


        }


        choices.appendChild(b)
    }

)
}


