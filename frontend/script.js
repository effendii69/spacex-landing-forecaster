// =========================
// SPACEX FALCON 9 RECOVERY OUTLOOK
// Launch Control Cinematic Edition
// By Azam Effendi - COMSATS '25
// Turning rocket science into intelligence
// =========================

const API_URL = window.location.origin;
let countdownInterval = null;
let rocketLaunchInterval = null;

// =========================
// CUSTOM CURSOR DOT TRACKING
// =========================
const cursorDot = document.querySelector('.cursor-dot');

if (cursorDot) {
  let mouseX = 0, mouseY = 0;
  let cursorX = 0, cursorY = 0;
  const speed = 0.15; // Smooth follow effect

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  function animateCursor() {
    const distX = mouseX - cursorX;
    const distY = mouseY - cursorY;
    
    cursorX += distX * speed;
    cursorY += distY * speed;
    
    cursorDot.style.left = cursorX + 'px';
    cursorDot.style.top = cursorY + 'px';
    
    requestAnimationFrame(animateCursor);
  }
  
  animateCursor();
}

// =========================
// FALCON 9 LOOPING LAUNCHES
// =========================
function initRocketLaunches() {
  const falcon9 = document.getElementById('falcon9Launch');
  if (!falcon9) return;

  // First launch happens immediately on page load
  setTimeout(() => {
    launchRocket();
  }, 1000);

  // Loop launches every 2 minutes (120 seconds)
  rocketLaunchInterval = setInterval(() => {
    launchRocket();
  }, 120000);
}

function launchRocket() {
  const falcon9 = document.getElementById('falcon9Launch');
  if (!falcon9) return;

  // Reset animation by cloning and replacing
  const newFalcon = falcon9.cloneNode(true);
  falcon9.parentNode.replaceChild(newFalcon, falcon9);
  
  console.log('🚀 Falcon 9 launch sequence initiated...');
}

// =========================
// FETCH LIVE DATA
// =========================
async function fetchLiveData() {
  try {
    const response = await fetch(`${API_URL}/api/next`);
    if (!response.ok) throw new Error('Failed to fetch live data');
    
    const data = await response.json();
    updateMissionCard(data);
    return data;
  } catch (error) {
    console.error('Error fetching live data:', error);
    return null;
  }
}

// =========================
// UPDATE MISSION CARD
// =========================
function updateMissionCard(data) {
  if (!data) return;

  // Update mission name
  const missionNameEl = document.getElementById('mission-name');
  if (missionNameEl && data.mission) {
    missionNameEl.textContent = data.mission;
  }

  // Update booster info
  const boosterPillEl = document.getElementById('booster-pill');
  if (boosterPillEl && data.booster) {
    boosterPillEl.textContent = `Booster ${data.booster}`;
  }

  // Update wind conditions
  const windPillEl = document.getElementById('wind-pill');
  if (windPillEl && data.wind_kts !== undefined) {
    windPillEl.textContent = `${data.wind_kts} kts wind`;
  }

  // Update probability with glow effect
  const probabilityEl = document.getElementById('probability');
  if (probabilityEl && data.probability !== undefined) {
    const prob = (data.probability * 100).toFixed(1);
    probabilityEl.innerHTML = `<span class="prob-value">${prob}</span><span class="prob-percent">%</span>`;
    
    // Change color based on probability
    if (data.probability >= 0.8) {
      probabilityEl.style.background = 'linear-gradient(135deg, var(--success), var(--cyan))';
    } else if (data.probability >= 0.5) {
      probabilityEl.style.background = 'linear-gradient(135deg, #ffaa00, var(--cyan))';
    } else {
      probabilityEl.style.background = 'linear-gradient(135deg, var(--failure), #ff8800)';
    }
    probabilityEl.style.webkitBackgroundClip = 'text';
    probabilityEl.style.webkitTextFillColor = 'transparent';
    probabilityEl.style.backgroundClip = 'text';
  }

  // Update details
  const detailsEl = document.getElementById('details');
  if (detailsEl) {
    const parts = [
      data.wind_kts ? `${data.wind_kts} kts crosswind` : null,
      data.countdown || null,
      data.booster || null
    ].filter(Boolean);
    detailsEl.textContent = parts.join(' | ') || 'Forecast lock: calm seas | droneship on station';
  }

  // Start countdown if launch time available
  if (data.countdown) {
    startCountdown(data.countdown);
  }
}

// =========================
// LIVE COUNTDOWN TIMER
// =========================
function startCountdown(initialCountdown) {
  if (countdownInterval) clearInterval(countdownInterval);
  
  const countdownPillEl = document.getElementById('countdown-pill');
  if (!countdownPillEl) return;

  countdownPillEl.textContent = initialCountdown;
  
  // Simple countdown display (static for now since we don't have exact launch time from API)
  // In a real implementation, you'd parse the countdown and update it every second
}

// =========================
// FETCH HISTORICAL DATA
// =========================
async function fetchHistoricalData() {
  try {
    const response = await fetch(`${API_URL}/api/history`);
    if (!response.ok) throw new Error('Failed to fetch historical data');
    
    const data = await response.json();
    renderChart(data);
    return data;
  } catch (error) {
    console.error('Error fetching historical data:', error);
    return null;
  }
}

// =========================
// RENDER PLOTLY CHART WITH ANIMATIONS
// =========================
function renderChart(data) {
  if (!data || !Array.isArray(data) || data.length === 0) return;

  const successful = {
    x: [],
    y: [],
    mode: 'markers',
    type: 'scatter',
    name: 'Successful',
    marker: {
      size: 10,
      color: '#00ff88',
      symbol: 'circle',
      line: {
        color: '#00ff88',
        width: 2
      },
      opacity: 0
    },
    hovertemplate: '<b>Flight %{x}</b><br>Payload: %{y:.0f} kg<br>Status: Success<extra></extra>'
  };

  const failed = {
    x: [],
    y: [],
    mode: 'markers',
    type: 'scatter',
    name: 'Failed/Expended',
    marker: {
      size: 10,
      color: '#ff4444',
      symbol: 'x',
      line: {
        color: '#ff4444',
        width: 2
      },
      opacity: 0
    },
    hovertemplate: '<b>Flight %{x}</b><br>Payload: %{y:.0f} kg<br>Status: Failed<extra></extra>'
  };

  // Separate data by outcome
  data.forEach((entry) => {
    const isSuccess = entry.success === 1 || entry.success === true || entry.success === '1';
    const flight = entry.FlightNumber || entry.flight;
    const mass = entry.PayloadMass || entry.mass || 0;
    
    if (isSuccess) {
      successful.x.push(flight);
      successful.y.push(mass);
    } else {
      failed.x.push(flight);
      failed.y.push(mass);
    }
  });

  const layout = {
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: 'Space Grotesk, sans-serif',
      color: '#999999',
      size: 12
    },
    xaxis: {
      title: 'Flight Number',
      gridcolor: 'rgba(255,255,255,0.05)',
      zerolinecolor: 'rgba(255,255,255,0.1)',
      tickfont: { size: 11 }
    },
    yaxis: {
      title: 'Payload Mass (kg)',
      gridcolor: 'rgba(255,255,255,0.05)',
      zerolinecolor: 'rgba(255,255,255,0.1)',
      tickfont: { size: 11 }
    },
    hovermode: 'closest',
    showlegend: false,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    hoverlabel: {
      bgcolor: 'rgba(15,15,15,0.95)',
      bordercolor: '#00ffff',
      font: { size: 12, family: 'Space Grotesk' }
    }
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  // Initial render with opacity 0
  Plotly.newPlot('chart', [successful, failed], layout, config);

  // Animate points appearing one by one
  animateChartPoints(successful.x.length + failed.x.length);
}

// =========================
// ANIMATE CHART POINTS
// =========================
function animateChartPoints(totalPoints) {
  if (totalPoints === 0) return;
  
  const duration = 2000; // 2 seconds total
  const interval = duration / totalPoints;
  let count = 0;

  const animate = setInterval(() => {
    count++;
    const opacity = Math.min(count / totalPoints, 1);
    
    Plotly.restyle('chart', {
      'marker.opacity': [opacity, opacity]
    });

    if (count >= totalPoints) {
      clearInterval(animate);
    }
  }, interval);
}

// =========================
// INITIALIZE APP
// =========================
async function init() {
  console.log('🚀 SpaceX Falcon 9 Recovery Outlook - Launch Control Active...');
  console.log('👨‍💻 Designed by Azam Effendi - COMSATS University \'25');
  
  // Initialize rocket launch sequence
  initRocketLaunches();
  
  // Fetch data in parallel
  const [liveData, historicalData] = await Promise.all([
    fetchLiveData(),
    fetchHistoricalData()
  ]);

  // Refresh live data every 30 seconds
  setInterval(fetchLiveData, 30000);
  
  console.log('✅ All systems operational');
}

// =========================
// START APPLICATION
// =========================
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
