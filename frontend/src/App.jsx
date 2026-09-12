import { useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Gauge,
  MapPin,
  Radio,
  ShieldCheck,
  Zap,
  Clock3,
  Wifi,
  WifiOff,
  Network,
  Bell,
  Settings,
} from "lucide-react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";


/* =========================================================
   ASSETS
========================================================= */

const backgroundImage = "/background.jpg";
const teamLogo = "/logo.png";


/* =========================================================
   BACKEND
========================================================= */

const API_URL = "http://localhost:5000";


/* =========================================================
   MAP CONTROLLER
========================================================= */

function MapController({ meter }) {

  const map = useMap();

  useEffect(() => {

    const latitude = meter?.location?.latitude;
    const longitude = meter?.location?.longitude;

    if (
      latitude !== null &&
      latitude !== undefined &&
      longitude !== null &&
      longitude !== undefined
    ) {
      map.flyTo(
        [latitude, longitude],
        13,
        {
          duration: 0.8,
        }
      );
    }

  }, [meter, map]);

  return null;
}


/* =========================================================
   STATUS TYPE
========================================================= */

function getStatusType(meter) {

  const priority =
    meter?.decision?.priority;

  const status =
    meter?.decision?.final_status;


  if (
    priority === "CRITICAL" ||
    priority === "HIGH" ||
    status === "FAULT DETECTED" ||
    status === "HIGH PRIORITY ALERT"
  ) {
    return "fault";
  }


  if (
    priority === "MEDIUM" ||
    status === "SUSPICIOUS"
  ) {
    return "suspicious";
  }


  return "normal";
}


/* =========================================================
   STATUS TEXT
========================================================= */

function getStatusText(meter) {

  const type =
    getStatusType(meter);


  if (type === "fault") {
    return "FAULT";
  }


  if (type === "suspicious") {
    return "SUSPICIOUS";
  }


  return "NORMAL";
}


/* =========================================================
   APP
========================================================= */

function App() {

  const [dashboard, setDashboard] =
    useState(null);

  const [selectedMeter, setSelectedMeter] =
    useState("M001");

  const [error, setError] =
    useState(null);

  const [lastUpdate, setLastUpdate] =
    useState(null);


  /* =======================================================
     FETCH DASHBOARD
  ======================================================= */

  async function fetchDashboard() {

    try {

      const response =
        await fetch(
          `${API_URL}/api/dashboard`
        );


      if (!response.ok) {

        throw new Error(
          `Backend returned ${response.status}`
        );

      }


      const data =
        await response.json();


      setDashboard(data);

      setError(null);

      setLastUpdate(
        new Date()
      );

    }

    catch (err) {

      console.error(
        "Dashboard error:",
        err
      );

      setError(
        "Backend connection lost"
      );

    }

  }


  /* =======================================================
     AUTO REFRESH
  ======================================================= */

  useEffect(() => {

    fetchDashboard();

    const interval =
      setInterval(
        fetchDashboard,
        1000
      );

    return () =>
      clearInterval(interval);

  }, []);


  /* =======================================================
     LOADING
  ======================================================= */

  if (!dashboard) {

    return (

      <div
        className="loading-screen"
        style={{
          backgroundImage:
            `linear-gradient(
              rgba(10,41,71,.76),
              rgba(6,28,49,.96)
            ),
            url(${backgroundImage})`,
        }}
      >

        <div className="loading-card">

          <img
            src={teamLogo}
            alt="Turing Spark"
            className="loading-logo"
          />

          <div className="loading-spinner">
            <Activity size={32} />
          </div>

          <h2>
            SIH Smart Electrical Monitoring
          </h2>

          <p>
            Connecting to monitoring backend...
          </p>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

        </div>

      </div>

    );

  }


  /* =======================================================
     METERS
  ======================================================= */

  const meters =
    dashboard.meters || [];


  if (meters.length === 0) {

    return (

      <div className="loading-screen">

        <div className="loading-card">

          <img
            src={teamLogo}
            alt="Turing Spark"
            className="loading-logo"
          />

          <Radio size={42} />

          <h2>
            Waiting for ESP32
          </h2>

          <p>
            No meter data received yet.
          </p>

        </div>

      </div>

    );

  }


  let meter =
    meters.find(
      item =>
        item.meter_id ===
        selectedMeter
    );


  if (!meter) {
    meter = meters[0];
  }


  /* =======================================================
     DATA
  ======================================================= */

  const readings =
    meter.readings || {};

  const electrical =
    meter.electrical || {};

  const model1 =
    meter.model1 || {};

  const model2 =
    meter.model2 || {};

  const decision =
    meter.decision || {};

  const liveHistory =
    meter.live_history || [];

  const location =
    meter.location || {};


  const voltage =
    Number(
      electrical.voltage_V || 0
    );

  const current =
    Number(
      electrical.current_A || 0
    );

  const power =
    Number(
      electrical.power_W || 0
    );


  const model1Prediction =
    model1.prediction ||
    "WAITING";

  const model2Prediction =
    model2.prediction ||
    "WAITING";


  const finalStatus =
    decision.final_status ||
    "MONITORING";


  const priority =
    decision.priority ||
    "LOW";


  const faultType =
    decision.fault_type ||
    model2.fault_type ||
    null;


  const statusType =
    getStatusType(meter);


  /* =======================================================
     LIVE CHART
  ======================================================= */

  const liveChartData =
    liveHistory.map(
      (item, index) => ({
        reading:
          index + 1,

        power:
          Number(
            item.power_W || 0
          ),

        current:
          Number(
            item.current_A || 0
          ),

        voltage:
          Number(
            item.voltage_V || 0
          ),
      })
    );


  /* =======================================================
     CONSUMPTION CHART
  ======================================================= */

  const consumptionHistory =
    model1.consumption_history ||
    [];


  const consumptionData =
    consumptionHistory.map(
      (value, index) => ({
        day:
          `D${index + 1}`,

        consumption:
          Number(value),
      })
    );


  /* =======================================================
     MAP
  ======================================================= */

  const latitude =
    location.latitude;

  const longitude =
    location.longitude;


  const mapCenter =
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined

      ? [
          latitude,
          longitude,
        ]

      : [
          21.2514,
          81.6296,
        ];


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div
      className="app"
      style={{
        "--dashboard-bg":
          `url(${backgroundImage})`,
      }}
    >

      <div className="background-layer"></div>


      {/* ==================================================
          SIDEBAR
      ================================================== */}

      <aside className="sidebar">

        <div className="brand">

          <img
            src={teamLogo}
            alt="Turing Spark"
            className="team-logo"
          />

        </div>


        <nav className="sidebar-nav">

          <div className="nav-item active">
            <Gauge size={20} />
            <span>Dashboard</span>
          </div>


          <div className="nav-item">
            <Activity size={20} />
            <span>Live Monitoring</span>
          </div>


          <div className="nav-item">
            <ShieldCheck size={20} />
            <span>AI Detection</span>
          </div>


          <div className="nav-item">
            <MapPin size={20} />
            <span>Meter Locations</span>
          </div>


          <div className="nav-item">
            <Network size={20} />
            <span>Meter Network</span>
          </div>


          <div className="nav-item">
            <Bell size={20} />
            <span>Alerts & Logs</span>
          </div>


          <div className="nav-item">
            <Settings size={20} />
            <span>Settings</span>
          </div>

        </nav>


        <div className="sidebar-bottom">

          <div className="backend-card">

            <div className="backend-status">

              <span className="live-dot"></span>

              Backend Online

            </div>

            <div className="backend-text">
              ESP32 • Flask • AI
            </div>

          </div>


          <div className="sidebar-footer-text">
            SIH Smart Electrical Monitoring
          </div>

        </div>

      </aside>


      {/* ==================================================
          MAIN
      ================================================== */}

      <main className="main">


        {/* HEADER */}

        <header className="topbar">

          <div>

            <div className="title-row">

              <Zap size={30} />

              <h1>
                Electrical Monitoring Dashboard
              </h1>

            </div>


            <p>
              Real-time intelligent electrical monitoring
            </p>

          </div>


          <div className="topbar-right">

            <div className="live-badge">

              <span className="live-dot"></span>

              LIVE

            </div>


            <div className="time-display">

              <Clock3 size={17} />

              {lastUpdate
                ? lastUpdate.toLocaleTimeString()
                : "--"
              }

            </div>

          </div>

        </header>


        {/* =================================================
            METER SELECTOR
        ================================================= */}

        <section className="meter-toolbar">

          <div className="meter-selector">

            <span>
              SELECT METER
            </span>


            <select
              value={meter.meter_id}
              onChange={
                e =>
                  setSelectedMeter(
                    e.target.value
                  )
              }
            >

              {meters.map(item => (

                <option
                  key={item.meter_id}
                  value={item.meter_id}
                >
                  {item.meter_id}
                </option>

              ))}

            </select>

          </div>


          <div className="connection-status">

            {meter.online !== false ? (

              <>
                <Wifi size={18} />

                Meter {meter.meter_id}

                <span className="live-dot"></span>

                Online
              </>

            ) : (

              <>
                <WifiOff size={18} />

                Meter {meter.meter_id}

                <span className="offline-dot"></span>

                Offline
              </>

            )}

          </div>

        </section>


        {/* =================================================
            ELECTRICAL CARDS
        ================================================= */}

        <section className="cards-grid">


          {/* VOLTAGE */}

          <div className="metric-card voltage-card">

            <div className="metric-header">

              <span>Voltage</span>

              <div className="metric-icon cream-icon">
                <Zap size={21} />
              </div>

            </div>


            <div className="metric-value">

              {voltage.toFixed(1)}

              <small>V</small>

            </div>


            <div className="metric-label">
              Calibrated supply voltage
            </div>

          </div>


          {/* CURRENT */}

          <div className="metric-card current-card">

            <div className="metric-header">

              <span>Current</span>

              <div className="metric-icon sage-icon">
                <Activity size={21} />
              </div>

            </div>


            <div className="metric-value">

              {current.toFixed(3)}

              <small>A</small>

            </div>


            <div className="metric-label">
              Estimated RMS current
            </div>

          </div>


          {/* POWER */}

          <div className="metric-card power-card">

            <div className="metric-header">

              <span>Power</span>

              <div className="metric-icon brown-icon">
                <Gauge size={21} />
              </div>

            </div>


            <div className="metric-value">

              {power.toFixed(1)}

              <small>W</small>

            </div>


            <div className="metric-label">
              Estimated electrical load
            </div>

          </div>


          {/* STATUS */}

          <div
            className={
              `metric-card status-card ${statusType}`
            }
          >

            <div className="metric-header">

              <span>
                System Status
              </span>


              {statusType === "normal"

                ? <CheckCircle2 size={23} />

                : <AlertTriangle size={23} />

              }

            </div>


            <div className="status-value">
              {finalStatus}
            </div>


            {faultType && (

              <div className="fault-type-main">

                FAULT TYPE:

                <strong>
                  {faultType.replace(
                    "FAULT_",
                    ""
                  )}
                </strong>

              </div>

            )}


            <div className="metric-label">
              Priority: {priority}
            </div>

          </div>

        </section>


        {/* =================================================
            LIVE + AI
        ================================================= */}

        <section className="two-column">


          {/* LIVE */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <h2>
                  Live Electrical Readings
                </h2>

                <p>
                  Real-time sensor monitoring
                </p>

              </div>

              <Activity size={23} />

            </div>


            <div className="live-stats">

              <div>

                <span>VOLTAGE</span>

                <strong>
                  {voltage.toFixed(1)} V
                </strong>

              </div>


              <div>

                <span>CURRENT</span>

                <strong>
                  {current.toFixed(3)} A
                </strong>

              </div>


              <div>

                <span>POWER</span>

                <strong>
                  {power.toFixed(1)} W
                </strong>

              </div>

            </div>


            <div className="chart-container">

              {liveChartData.length > 0 ? (

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <LineChart
                    data={liveChartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="reading"
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="power"
                      name="Power (W)"
                      stroke="#D3D4C0"
                      strokeWidth={3}
                      dot={false}
                      isAnimationActive={false}
                    />

                  </LineChart>

                </ResponsiveContainer>

              ) : (

                <div className="empty-chart">
                  Waiting for live readings...
                </div>

              )}

            </div>

          </div>


          {/* AI */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <h2>
                  AI Detection
                </h2>

                <p>
                  Dual-model intelligent analysis
                </p>

              </div>

              <Cpu size={23} />

            </div>


            <div className="ai-results">


              {/* MODEL 1 */}

              <div className="ai-row">

                <div className="ai-name">

                  <div className="ai-number">
                    01
                  </div>

                  <div>

                    <strong>
                      Consumption Model
                    </strong>

                    <small>
                      SGCC historical analysis
                    </small>

                  </div>

                </div>


                <span
                  className={
                    `prediction ${
                      model1Prediction.toLowerCase()
                    }`
                  }
                >
                  {model1Prediction}
                </span>

              </div>


              {/* MODEL 2 */}

              <div className="ai-row">

                <div className="ai-name">

                  <div className="ai-number">
                    02
                  </div>

                  <div>

                    <strong>
                      Fault Detection Model
                    </strong>

                    <small>
                      Real-time transformer analysis
                    </small>

                  </div>

                </div>


                <span
                  className={
                    `prediction ${
                      model2Prediction.toLowerCase()
                    }`
                  }
                >
                  {model2Prediction}
                </span>

              </div>


              {/* FAULT */}

              {faultType && (

                <div className="fault-details">

                  <div>

                    <span>
                      DETECTED FAULT
                    </span>

                    <strong>
                      {faultType.replace(
                        "FAULT_",
                        ""
                      )}
                    </strong>

                  </div>


                  <div>

                    <span>
                      DETECTED BY
                    </span>

                    <strong>
                      MODEL 2
                    </strong>

                  </div>


                  <div>

                    <span>
                      PRIORITY
                    </span>

                    <strong>
                      {priority}
                    </strong>

                  </div>

                </div>

              )}


              {/* FINAL */}

              <div
                className={
                  `final-alert ${statusType}`
                }
              >

                <div>

                  <span>
                    FINAL DECISION
                  </span>

                  <strong>
                    {finalStatus}
                  </strong>


                  {faultType && (

                    <small>

                      Fault Type:{" "}

                      {faultType.replace(
                        "FAULT_",
                        ""
                      )}

                    </small>

                  )}

                </div>


                <div className="priority">
                  {priority}
                </div>

              </div>


              <div className="decision-message">
                {decision.message ||
                  "System monitoring active."}
              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            30 DAY
        ================================================= */}

        <section className="panel consumption-panel">

          <div className="panel-header">

            <div>

              <h2>
                30-Day Consumption Profile
              </h2>

              <p>
                Model 1 prototype consumption history
              </p>

            </div>

            <Activity size={23} />

          </div>


          <div className="large-chart">

            {consumptionData.length > 0 ? (

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <BarChart
                  data={consumptionData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="day"
                    interval={1}
                  />

                  <YAxis />

                  <Tooltip />

                  <Bar
                    dataKey="consumption"
                    name="Consumption"
                    fill="#8B5E3C"
                    radius={[
                      4,
                      4,
                      0,
                      0
                    ]}
                  />

                </BarChart>

              </ResponsiveContainer>

            ) : (

              <div className="empty-chart">
                Model 1 is collecting consumption history...
              </div>

            )}

          </div>

        </section>


        {/* =================================================
            TRANSMISSION + MAP
        ================================================= */}

        <section className="two-column bottom-section">


          {/* TRANSMISSION */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <h2>
                  Transmission Monitoring
                </h2>

                <p>
                  T1 / T2 / House sensor values
                </p>

              </div>

              <Radio size={23} />

            </div>


            <div className="transmission-table">

              <div className="table-row table-head">

                <span>POINT</span>

                <span>CURRENT</span>

                <span>VOLTAGE</span>

                <span>STATUS</span>

              </div>


              <div className="table-row">

                <strong>T1</strong>

                <span>
                  {readings.T1_CS ?? 0}
                </span>

                <span>
                  {readings.T1_VS ?? 0}
                </span>

                <span className="normal-text">
                  NORMAL
                </span>

              </div>


              <div className="table-row">

                <strong>T2</strong>

                <span>
                  {readings.T2_CS ?? 0}
                </span>

                <span>
                  {readings.T2_VS ?? 0}
                </span>

                <span className="normal-text">
                  NORMAL
                </span>

              </div>


              <div className="table-row">

                <strong>H1</strong>

                <span>
                  {readings.H1_CS ?? 0}
                </span>

                <span>
                  {readings.H1_VS ?? 0}
                </span>

                <span
                  className={
                    statusType === "fault"
                      ? "fault-text"
                      : "normal-text"
                  }
                >
                  {statusType === "fault"
                    ? "FAULT"
                    : "NORMAL"
                  }
                </span>

              </div>

            </div>

          </div>


          {/* MAP */}

          <div className="panel">

            <div className="panel-header">

              <div>

                <h2>
                  Meter Location
                </h2>

                <p>
                  Geographic monitoring
                </p>

              </div>

              <MapPin size={23} />

            </div>


            <div className="map-wrapper">

              <MapContainer
                center={mapCenter}
                zoom={13}
                scrollWheelZoom={true}
                className="map"
              >

                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />


                <MapController
                  meter={meter}
                />


                {meters.map(item => {

                  const itemLocation =
                    item.location;


                  if (
                    !itemLocation ||
                    itemLocation.latitude === null ||
                    itemLocation.longitude === null
                  ) {
                    return null;
                  }


                  const type =
                    getStatusType(item);


                  let markerColor =
                    "#22C55E";


                  if (type === "fault") {
                    markerColor =
                      "#EF4444";
                  }

                  else if (
                    type === "suspicious"
                  ) {
                    markerColor =
                      "#8B5E3C";
                  }


                  return (

                    <CircleMarker
                      key={item.meter_id}

                      center={[
                        itemLocation.latitude,
                        itemLocation.longitude
                      ]}

                      radius={
                        item.meter_id ===
                        meter.meter_id
                          ? 11
                          : 8
                      }

                      pathOptions={{
                        color:
                          markerColor,

                        fillColor:
                          markerColor,

                        fillOpacity:
                          0.85,

                        weight:
                          3
                      }}

                      eventHandlers={{
                        click: () =>
                          setSelectedMeter(
                            item.meter_id
                          )
                      }}
                    >

                      <Popup>

                        <div className="map-popup">

                          <strong>
                            {item.meter_id}
                          </strong>

                          <span>
                            {getStatusText(item)}
                          </span>


                          {item?.decision?.fault_type && (

                            <small>

                              Fault:{" "}

                              {
                                item.decision.fault_type
                                  .replace(
                                    "FAULT_",
                                    ""
                                  )
                              }

                            </small>

                          )}


                          <small>

                            {item.online !== false
                              ? "Online"
                              : "Offline"
                            }

                          </small>

                        </div>

                      </Popup>

                    </CircleMarker>

                  );

                })}

              </MapContainer>


              <div className="map-legend">

                <span>

                  <i className="legend-normal"></i>

                  Normal

                </span>


                <span>

                  <i className="legend-warning"></i>

                  Suspicious

                </span>


                <span>

                  <i className="legend-fault"></i>

                  Fault

                </span>

              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            NETWORK
        ================================================= */}

        <section className="panel network-panel">

          <div className="panel-header">

            <div>

              <h2>
                Connected Meter Network
              </h2>

              <p>
                Smart meters connected to the backend
              </p>

            </div>

            <Network size={23} />

          </div>


          <div className="network-grid">

            {meters.map(item => {

              const type =
                getStatusType(item);

              const fault =
                item?.decision?.fault_type;


              return (

                <button
                  key={item.meter_id}

                  className={
                    `network-meter ${
                      item.meter_id ===
                      meter.meter_id
                        ? "selected"
                        : ""
                    }`
                  }

                  onClick={() =>
                    setSelectedMeter(
                      item.meter_id
                    )
                  }
                >

                  <div className="network-top">

                    <div>

                      <Radio size={17} />

                      <strong>
                        {item.meter_id}
                      </strong>

                    </div>


                    <span
                      className={
                        `network-status ${type}`
                      }
                    >
                      {getStatusText(item)}
                    </span>

                  </div>


                  {fault && (

                    <div className="network-fault">

                      Fault:{" "}

                      {fault.replace(
                        "FAULT_",
                        ""
                      )}

                    </div>

                  )}


                  <div className="network-values">

                    <div>

                      <span>
                        POWER
                      </span>

                      <strong>

                        {Number(
                          item?.electrical?.power_W ||
                          0
                        ).toFixed(1)}

                        W

                      </strong>

                    </div>


                    <div>

                      <span>
                        MODEL 1
                      </span>

                      <strong>
                        {item?.model1?.prediction ||
                          "WAITING"}
                      </strong>

                    </div>


                    <div>

                      <span>
                        MODEL 2
                      </span>

                      <strong>
                        {item?.model2?.prediction ||
                          "WAITING"}
                      </strong>

                    </div>

                  </div>


                  <div className="network-bottom">

                    <span>

                      {item.online !== false
                        ? "● Online"
                        : "● Offline"
                      }

                    </span>


                    <span>

                      Priority:{" "}

                      {item?.decision?.priority ||
                        "LOW"}

                    </span>

                  </div>

                </button>

              );

            })}

          </div>

        </section>


        {/* FOOTER */}

        <footer>

          <span>
            TURING SPARK • SIH Smart Electrical Monitoring
          </span>

          <span>
            ESP32 • AI • IoT • Real-Time Monitoring
          </span>

        </footer>

      </main>

    </div>

  );
}


export default App;