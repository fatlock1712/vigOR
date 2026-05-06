/**
 * Client-side vigOR AI: Open-Meteo + Google Directions (Maps JS API) + MLC WebLLM.
 * Replaces Flask/Cloudflare Nemotron calls when user selects "This device (WebGPU)".
 */
import { CreateMLCEngine } from 'https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.78/+esm';

const MODEL_ID = 'Phi-3-mini-4k-instruct-q4f16_1-MLC';

let engineSingleton = null;
let enginePromise = null;

export const LOCAL_MODEL_LABEL =
  'Phi-3 Mini 4B (MLC WebGPU) — local inference; Nemotron naming in UI refers to this pipeline until MLC publishes Nemotron WebGPU bundles.';

function onProgressReport(cb, payload) {
  if (typeof cb === 'function') cb(payload);
}

async function getEngine(onProgress) {
  if (engineSingleton) return engineSingleton;
  if (!enginePromise) {
    enginePromise = CreateMLCEngine(MODEL_ID, {
      initProgressCallback: (p) => onProgressReport(onProgress, p)
    }).then((eng) => {
      engineSingleton = eng;
      return eng;
    });
  }
  return enginePromise;
}

function safeUser(userData) {
  const u = userData || {};
  const allergy = u.allergy;
  return {
    age: u.age ?? 30,
    asthma_severity: Number(u.asthma_severity ?? 0),
    allergy: Array.isArray(allergy) ? allergy.join(', ') || 'none' : allergy || 'none',
    heart_condition: u.heart_condition || 'none'
  };
}

async function llmChatJson(engine, systemPrompt, userPrompt, maxTokens, onProgress) {
  onProgressReport(onProgress, { text: 'Generating response…' });
  const reply = await engine.chat.completions.create({
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ],
    temperature: 0.2,
    max_tokens: maxTokens
  });
  let raw = reply.choices?.[0]?.message?.content ?? '';
  if (typeof raw !== 'string') raw = JSON.stringify(raw);
  return raw.trim();
}

function stripJsonFences(raw) {
  let t = raw.trim();
  if (t.startsWith('```json')) t = t.slice(7);
  else if (t.startsWith('```')) t = t.slice(3);
  if (t.endsWith('```')) t = t.slice(0, -3);
  return t.trim();
}

function parseJsonLoose(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    try {
      return JSON.parse(stripJsonFences(raw));
    } catch {
      const m = raw.match(/\{[\s\S]*\}/);
      if (m) return JSON.parse(m[0]);
      throw new Error('Model did not return valid JSON');
    }
  }
}

/* --- Open-Meteo environmental data (browser CORS–safe) --- */

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  return r.json();
}

async function openMeteoEnvAt(lat, lng, hourIndex = 2) {
  const fallback = () => ({
    temp: 70,
    humidity: 50,
    wind_speed: 5,
    pm25: 0,
    pm10: 0,
    no2: 0,
    o3: 0,
    tree_pollen: 0,
    weed_pollen: 0,
    grass_pollen: 0
  });

  const weatherUrl =
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}` +
    `&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m` +
    `&forecast_hours=${Math.max(6, hourIndex + 2)}&timezone=auto`;
  const airUrl =
    `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lng}` +
    `&hourly=pm2_5,pm10,ozone,nitrogen_dioxide,grass_pollen,birch_pollen,alder_pollen,mugwort_pollen,olive_pollen,ragweed_pollen` +
    `&forecast_hours=${Math.max(6, hourIndex + 2)}&timezone=auto`;

  const [w, a] = await Promise.all([
    fetchJson(weatherUrl).catch(() => null),
    fetchJson(airUrl).catch(() => null)
  ]);

  const wlen = w?.hourly?.time?.length ?? 0;
  const alen = a?.hourly?.time?.length ?? 0;
  if (!wlen && !alen) {
    return fallback();
  }
  const wi = wlen ? Math.min(Math.max(hourIndex, 0), wlen - 1) : 0;
  const ai = alen ? Math.min(Math.max(hourIndex, 0), alen - 1) : 0;

  const temp = w?.hourly?.temperature_2m?.[wi] ?? 70;
  const humidity = w?.hourly?.relative_humidity_2m?.[wi] ?? 50;
  const wind = w?.hourly?.wind_speed_10m?.[wi] ?? 5;

  const pm25 = a?.hourly?.pm2_5?.[ai] ?? 0;
  const pm10 = a?.hourly?.pm10?.[ai] ?? 0;
  const o3 = a?.hourly?.ozone?.[ai] ?? 0;
  const no2 = a?.hourly?.nitrogen_dioxide?.[ai] ?? 0;

  const tree =
    (a?.hourly?.birch_pollen?.[ai] ?? 0) +
    (a?.hourly?.alder_pollen?.[ai] ?? 0) +
    (a?.hourly?.olive_pollen?.[ai] ?? 0);
  const grass = a?.hourly?.grass_pollen?.[ai] ?? 0;
  const weed =
    (a?.hourly?.mugwort_pollen?.[ai] ?? 0) + (a?.hourly?.ragweed_pollen?.[ai] ?? 0);

  return {
    temp,
    humidity,
    wind_speed: wind,
    pm25,
    pm10,
    no2,
    o3,
    tree_pollen: tree,
    weed_pollen: weed,
    grass_pollen: grass
  };
}

async function fetchEnvForecastBundle(latitude, longitude) {
  const env2h = await openMeteoEnvAt(latitude, longitude, 2);
  return env2h;
}

function decodePolyline(encoded) {
  const points = [];
  let index = 0;
  let lat = 0;
  let lng = 0;
  const len = encoded.length;
  while (index < len) {
    let b;
    let shift = 0;
    let result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = (result & 1) !== 0 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = (result & 1) !== 0 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push({ lat: lat / 1e5, lng: lng / 1e5 });
  }
  return points;
}

function getSamplePointsFromEncoded(encodedPolyline) {
  const coords = decodePolyline(encodedPolyline);
  const pts = coords.length;
  if (pts === 0) return [];
  const indices = [0, Math.floor(pts * 0.25), Math.floor(pts * 0.5), Math.floor(pts * 0.75), pts - 1];
  return indices.map((i) => coords[i]);
}

function formatComprehensiveRoute(allCoords, envResults) {
  const n = allCoords.length;
  const ix = [0, Math.floor(n / 4), Math.floor(n / 2), Math.floor((3 * n) / 4), n - 1];
  const labels = ['Start', '25%', '50%', '75%', 'End'];
  const routeData = [];
  for (let i = 0; i < ix.length; i++) {
    const coord = allCoords[ix[i]];
    const env = envResults[i];
    routeData.push({
      stage: labels[i],
      coordinates: { lat: Math.round(coord.lat * 1e4) / 1e4, lng: Math.round(coord.lng * 1e4) / 1e4 },
      weather: { temp: env.temp, humidity: env.humidity, wind_speed: env.wind_speed },
      air_quality: { pm25: env.pm25, pm10: env.pm10, no2: env.no2, o3: env.o3 },
      pollen: {
        'tree (Universal Pollen Index)': env.tree_pollen,
        'weed (Universal Pollen Index)': env.weed_pollen,
        'grass (Universal Pollen Index)': env.grass_pollen
      }
    });
  }
  return routeData;
}

/* --- Bridge handlers --- */

async function bridgeGeneral(engine, payload, onProgress) {
  const user_prompt = payload.user_prompt ?? '';
  const chat_history = payload.chat_history ?? [];
  const systemPrompt =
    'You are the orchestration router for a medical-environmental app. Output ONLY compact JSON.';
  const userPrompt =
    '[SYSTEM ROLE]\n' +
    'Match user intent to exactly one tool.\n\n[TOOLS]\n' +
    '- find_route: travel/navigate/path between locations\n' +
    '- forecast: weather, air quality, pollen at a location\n' +
    '- wrong_feedback: unrelated / jokes / outside scope\n\n' +
    '[CHAT HISTORY]\n' +
    JSON.stringify(chat_history) +
    '\n[USER PROMPT]\n' +
    user_prompt +
    '\n\n[OUTPUT_SCHEMA] {"action":"find_route"|"forecast"|"wrong_feedback"}';
  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 256, onProgress);
  const data = parseJsonLoose(raw);
  return { action: data.action || 'wrong_feedback' };
}

async function bridgeAsking(engine, payload, onProgress) {
  const user_prompt = payload.user_prompt ?? '';
  const systemPrompt = 'Medical route agent. Output ONLY compact JSON.';
  const userPrompt =
    'Does the user accept proceeding after a risk warning? yes or no.\n' +
    'If ambiguous, answer no.\n[USER PROMPT]\n' +
    user_prompt +
    '\n{"decision":"yes"|"no"}';
  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 128, onProgress);
  const data = parseJsonLoose(raw);
  return { decision: (data.decision || 'no').toLowerCase() };
}

async function bridgeGoRespond(engine, payload, onProgress) {
  const systemPrompt =
    'You summarize route safety guidance for asthma/allergy patients. Output ONLY compact JSON.';
  const userPrompt =
    '[DATA_INPUT]\n' +
    JSON.stringify({
      recommended_route_id: payload.recommended_route_id,
      verdict: payload.verdict,
      medical_logic: payload.medical_logic,
      reasoning_summary: payload.reasoning_summary,
      warnings: payload.warnings
    }) +
    '\n{"response":"<message to user>"}';
  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 768, onProgress);
  const data = parseJsonLoose(raw);
  const msg = data.response || '';
  return { status: 'success', message: msg };
}

async function bridgeWaitRespond(engine, payload, onProgress) {
  const systemPrompt = 'Medical route agent. Plain language warnings. Output ONLY compact JSON.';
  const userPrompt =
    '[DATA_INPUT]\n' +
    JSON.stringify({
      medical_logic: payload.medical_logic,
      reasoning_summary: payload.reasoning_summary,
      warnings: payload.warnings,
      suggestion: payload.suggestion
    }) +
    '\n{"response":"<empathetic message including wait suggestions and explicit risk question>"}';
  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 900, onProgress);
  const data = parseJsonLoose(raw);
  return { status: 'success', message: data.response || '' };
}

async function bridgeEnvForecast(engine, payload, onProgress) {
  const latitude = payload.latitude;
  const longitude = payload.longitude;
  const user_data = safeUser(payload.user_data);
  const env2h = await fetchEnvForecastBundle(latitude, longitude);
  const llm_payload = {
    location_context_in_2_hours: {
      weather: { temp: env2h.temp, humidity: env2h.humidity, wind_speed: env2h.wind_speed },
      air_quality: { pm25: env2h.pm25, pm10: env2h.pm10, no2: env2h.no2, o3: env2h.o3 },
      pollen: {
        tree_pollen: env2h.tree_pollen,
        weed_pollen: env2h.weed_pollen,
        grass_pollen: env2h.grass_pollen
      }
    },
    user_context: {
      user_age: user_data.age,
      'user_asthma_severity(0-4)': user_data.asthma_severity,
      user_allergy: user_data.allergy,
      heart_condition: user_data.heart_condition
    }
  };
  const systemPrompt =
    'Environmental Health Advisor using Open-Meteo style data only. Output ONLY compact JSON.';
  const userPrompt =
    'Analyze 2-hour outlook vs user respiratory profile. No hallucinated numbers beyond input.\n' +
    JSON.stringify(llm_payload, null, 2) +
    '\n{"response":"<single cohesive forecast string>"}';
  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 900, onProgress);
  const data = parseJsonLoose(raw);
  const text = data.response || 'Forecast unavailable.';
  return { status: 'success', data: text };
}

async function bridgeGetRoutes(engine, payload, onProgress) {
  const origin = payload.origin;
  const destination = payload.destination;
  const transport = payload.transport || 'walking';
  const user_data = safeUser(payload.user_data);
  const fetchDirs = globalThis.__vigorFetchDirectionRoutes;
  if (typeof fetchDirs !== 'function') {
    throw new Error('Maps Directions not ready. Wait for the map to load and try again.');
  }
  onProgressReport(onProgress, { text: 'Fetching route alternatives…' });
  const routeList = await fetchDirs(origin, destination, transport);
  if (!routeList?.length) throw new Error('No routes returned from Directions API.');

  const polylinesMap = {};
  const allRoutesData = [];

  for (const r of routeList) {
    polylinesMap[r.route_id] = r.encodedPolyline;
    const sampleCoords = getSamplePointsFromEncoded(r.encodedPolyline);
    onProgressReport(onProgress, { text: 'Sampling air & weather along route ' + r.route_id + '…' });
    const envResults = await Promise.all(
      sampleCoords.map((pt) => openMeteoEnvAt(pt.lat, pt.lng, 2))
    );
    const routeDetails = formatComprehensiveRoute(sampleCoords, envResults);
    allRoutesData.push({
      route_id: r.route_id,
      route_label: 'Route ' + r.route_id,
      checkpoints: routeDetails
    });
  }

  const travelMode = { driving: 'DRIVE', biking: 'BICYCLE', walking: 'WALK' }[String(transport).toLowerCase()] || 'WALK';
  const llm_payload = {
    trip_context: {
      transport: travelMode,
      user_age: user_data.age,
      'user_asthma(from 0 to 4)': user_data.asthma_severity,
      user_allergy: user_data.allergy,
      heart_condition: user_data.heart_condition
    },
    alternatives: allRoutesData
  };

  const systemPrompt =
    'Medical & Environmental Intelligence Agent. Use only numbers in data. Output ONLY valid JSON matching schema.';
  const userPrompt =
    JSON.stringify(llm_payload, null, 2) +
    '\n\n[OUTPUT_SCHEMA]\n' +
    '{\n' +
    '  "action": "Go" or "Wait",\n' +
    '  "recommended_route_id": <integer>,\n' +
    '  "verdict": "Safe" | "Caution" | "Danger",\n' +
    '  "medical_logic": "<string>",\n' +
    '  "reasoning_summary": "<string>",\n' +
    '  "warnings": ["<string>",...],\n' +
    '  "suggestion": ["<string>",...]\n' +
    '}\n';

  const raw = await llmChatJson(engine, systemPrompt, userPrompt, 3500, onProgress);
  const responseData = parseJsonLoose(raw);
  const chosenId = responseData.recommended_route_id;
  responseData.recommended_polyline = chosenId ? polylinesMap[chosenId] : null;
  responseData.unchosen_polylines = Object.entries(polylinesMap)
    .filter(([k]) => Number(k) !== Number(chosenId))
    .map(([, poly]) => poly);

  return { status: 'success', data: responseData };
}

export async function runBridge(endpoint, payload, options = {}) {
  const onProgress = options.onProgress;
  const engine = await getEngine(onProgress);

  switch (endpoint) {
    case 'general_response':
      return bridgeGeneral(engine, payload, onProgress);
    case 'asking_response':
      return bridgeAsking(engine, payload, onProgress);
    case 'GO_respond_user':
      return bridgeGoRespond(engine, payload, onProgress);
    case 'WAIT_respond_user':
      return bridgeWaitRespond(engine, payload, onProgress);
    case 'get_env_forecast':
      return bridgeEnvForecast(engine, payload, onProgress);
    case 'get_routes':
      return bridgeGetRoutes(engine, payload, onProgress);
    default:
      throw new Error('Unknown endpoint: ' + endpoint);
  }
}
