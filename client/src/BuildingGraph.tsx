import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";

const JSON_PATH = "/complex_graph_example.json";

// ────────────────────────────────────────────────
// Типы и классы
// ────────────────────────────────────────────────

interface NodeTypeConfig {
    label: string;
    color: string;
    shape: "circle" | "rect" | "diamond" | "hexagon";
    r: number;
    layer: string;
}

interface EdgeTypeConfig {
    label: string;
    color: string;
    dash: string;
    width: number;
}

interface NodeParams {
    label?: string;
    layer?: number;
    section?: number;
    floor?: number;
}

export class NodeType {
    constructor(public id: string, public config: NodeTypeConfig) {}
    get label() { return this.config.label; }
    get color() { return this.config.color; }
    get shape() { return this.config.shape; }
    get r() { return this.config.r; }
}

export class EdgeType {
    constructor(public id: string, public config: EdgeTypeConfig) {}
    get label() { return this.config.label; }
    get color() { return this.config.color; }
    get dash() { return this.config.dash; }
    get width() { return this.config.width; }
}

export class GraphNode {
    public id: string;
    public type: NodeType;
    public label: string;
    public layer: number;
    public section: number;
    public floor: number;
    public jsonX: number = 0;
    public jsonY: number = 0;
    public jsonZ: number = 0;
    x: number = 0;
    y: number = 0;

    constructor(id: string, type: NodeType, params: NodeParams = {}) {
        this.id = id;
        this.type = type;
        this.label = params.label || type.label;
        this.layer = params.layer ?? 0;
        this.section = params.section ?? -1;
        this.floor = params.floor ?? 0;
    }
}

export class GraphEdge {
    constructor(public source: string, public target: string, public type: EdgeType) {}
}

interface D3Node extends GraphNode { x: number; y: number; }
interface D3Edge { source: D3Node; target: D3Node; type: EdgeType; }

interface BuildingParams {
    floors: number;
    sections: number;
    aptsPerFloor: number;
    liftsPerSection: number;
    risersPerSection: number;
}

// ────────────────────────────────────────────────
// Константы
// ────────────────────────────────────────────────

export const NODE_TYPES: Record<string, NodeType> = {
    APT:   new NodeType("APT",   { label: "Квартира",   color: "#4A9EFF", shape: "rect",    r: 10, layer: "floor" }),
    MOP:   new NodeType("MOP",   { label: "МОП",        color: "#22D3A0", shape: "rect",    r: 12, layer: "floor" }),
    LIFT:  new NodeType("LIFT",  { label: "Лифт",       color: "#F5A623", shape: "circle",  r: 10, layer: "floor" }),
    RISER: new NodeType("RISER", { label: "Стояк",      color: "#B06AFF", shape: "diamond", r: 9,  layer: "vertical" }),
    PANEL: new NodeType("PANEL", { label: "Эл. щит",    color: "#FF6B6B", shape: "hexagon", r: 11, layer: "tech" }),
    ITP:   new NodeType("ITP",   { label: "ИТП",        color: "#FF9F43", shape: "hexagon", r: 14, layer: "basement" }),
    TECH:  new NodeType("TECH",  { label: "Тех. помещение", color: "#82B9FF", shape: "rect", r: 13, layer: "basement" }),
    ROOF:  new NodeType("ROOF",  { label: "Тех. этаж/кровля", color: "#A29BFE", shape: "rect", r: 13, layer: "roof" }),
};

export const EDGE_TYPES: Record<string, EdgeType> = {
    ADJ:   new EdgeType("ADJ",   { label: "Смежность",           color: "#4A9EFF44", dash: "",    width: 2 }),
    HEAT:  new EdgeType("HEAT",  { label: "Теплоснабжение",      color: "#FF6B6BCC", dash: "6,3",  width: 2 }),
    COLD:  new EdgeType("COLD",  { label: "Хол. водоснабжение",  color: "#4A9EFFCC", dash: "6,3",  width: 2 }),
    HOT:   new EdgeType("HOT",   { label: "Гор. водоснабжение",  color: "#FF9F43CC", dash: "6,3",  width: 2 }),
    ELEC:  new EdgeType("ELEC",  { label: "Электроснабжение",    color: "#FFD32ACC", dash: "4,2",  width: 2 }),
};

const NODE_TYPE_MAPPING: Record<string, NodeType> = {
    TechNode: NODE_TYPES.TECH, ElecNode: NODE_TYPES.PANEL, MopNode: NODE_TYPES.MOP,
    ElevNode: NODE_TYPES.LIFT, FlatNode: NODE_TYPES.APT, RiserNode: NODE_TYPES.RISER, ITPNode: NODE_TYPES.ITP,
};

const EDGE_TYPE_MAPPING: Record<string, EdgeType> = {
    PathEdge: EDGE_TYPES.ADJ, ElecEdge: EDGE_TYPES.ELEC, HotWaterEdge: EDGE_TYPES.HOT, ColdWaterEdge: EDGE_TYPES.COLD,
};

function project3D(jx: number, jy: number, jz: number, cx: number, cy: number, cz: number, scale: number, rotX: number, rotY: number) {
    const dx = jx - cx, dy = jy - cy, dz = jz - cz;
    const rY = rotY * Math.PI / 180, rX = rotX * Math.PI / 180;
    let x1 = dx * Math.cos(rY) - dy * Math.sin(rY);
    let y1 = dx * Math.sin(rY) + dy * Math.cos(rY);
    let y2 = y1 * Math.cos(rX) - dz * Math.sin(rX);
    return { sx: x1 * scale, sy: y2 * scale };
}

export default function BuildingGraph({ houseIndex = 0 }: { houseIndex?: number }) {
    const svgRef = useRef<SVGSVGElement | null>(null);
    const zoomRef = useRef<any>(null);

    const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
    const [buildingParams, setBuildingParams] = useState<BuildingParams>({ floors: 0, sections: 0, aptsPerFloor: 0, liftsPerSection: 0, risersPerSection: 0 });

    const [activeEdgeTypes, setActiveEdgeTypes] = useState<Record<string, boolean>>(Object.fromEntries(Object.keys(EDGE_TYPES).map(k => [k, true])));
    const [activeNodeTypes, setActiveNodeTypes] = useState<Record<string, boolean>>(Object.fromEntries(Object.keys(NODE_TYPES).map(k => [k, true])));

    const [isAutoRotating, setIsAutoRotating] = useState(false);
    const [hovered, setHovered] = useState<GraphNode | null>(null);
    const [loading, setLoading] = useState(true);
    const [mode, setMode] = useState<'original' | 'forecast'>('original');
    const [riskProbs, setRiskProbs] = useState<Record<string, number>>({});
    const [repairedNodes, setRepairedNodes] = useState<Set<string>>(new Set());
    const [isSimulating, setIsSimulating] = useState(false);

    const rotXRef = useRef(35);
    const rotYRef = useRef(45);
    const brigade3DRef = useRef<{ jsonX: number; jsonY: number; jsonZ: number } | null>(null);
    const brigadeAdjRef = useRef<Map<string, string[]>>(new Map());

    useEffect(() => {
        setLoading(true);
        d3.json(JSON_PATH).then((data: any) => {
            const house = data?.houses?.[houseIndex];
            if (!house) return;

            const nodes: GraphNode[] = house.nodes.map((jn: any) => {
                const f = jn.features || {};
                const n = new GraphNode(String(jn.id), NODE_TYPE_MAPPING[jn.type] || NODE_TYPES.TECH, {
                    label: jn.type, floor: f.floor ?? 0, section: f.section ?? -1
                });
                n.jsonX = f.x ?? 0; n.jsonY = f.y ?? 0; n.jsonZ = f.z ?? 0;
                return n;
            });

            const edges: GraphEdge[] = house.edges.map((je: any) =>
                new GraphEdge(String(je.source), String(je.target), EDGE_TYPE_MAPPING[je.type] || EDGE_TYPES.ADJ)
            );

            setGraphData({ nodes, edges });

            // Вычисление параметров дома на основе графа
            const maxFloor = Math.max(...nodes.map(n => n.floor), 0);
            const sectionsSet = new Set(nodes.map(n => n.section).filter(s => s >= 0));
            const totalSections = sectionsSet.size || 1;

            const totalApts = nodes.filter(n => n.type.id === "APT").length;
            const avgAptsPerFloor = maxFloor > 0 ? Math.round((totalApts / maxFloor) / totalSections) : 0;

            const totalLifts = nodes.filter(n => n.type.id === "LIFT").length;
            const liftsPerSec = Math.round(totalLifts / totalSections) || 1;

            const totalRisers = nodes.filter(n => n.type.id === "RISER").length;
            const risersPerSec = Math.round(totalRisers / totalSections) || 1;

            setBuildingParams({
                floors: maxFloor,
                sections: totalSections,
                aptsPerFloor: avgAptsPerFloor || 4,
                liftsPerSection: liftsPerSec,
                risersPerSection: risersPerSec
            });

            const adj = new Map<string, string[]>();
            nodes.forEach(n => adj.set(n.id, []));
            edges.forEach(e => {
                if (e.type.id === "ADJ" || e.type.id === "HOT") {
                    adj.get(e.source)?.push(e.target); adj.get(e.target)?.push(e.source);
                }
            });
            brigadeAdjRef.current = adj;

            // Установка начальной позиции бригады в TECH
            const startNode = nodes.find(n => n.type.id === "TECH") || nodes[0];
            if (startNode) {
                brigade3DRef.current = { jsonX: startNode.jsonX, jsonY: startNode.jsonY, jsonZ: startNode.jsonZ };
            }

            setLoading(false);
        });
    }, [houseIndex]);

    useEffect(() => {
        if (loading || !graphData.nodes.length || !svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();
        const width = svgRef.current.clientWidth;
        const height = svgRef.current.clientHeight;
        const g = svg.append("g");

        svg.on("contextmenu", (e) => e.preventDefault());

        const fNodes = graphData.nodes.filter(n => activeNodeTypes[n.type.id]);
        const fNodeIds = new Set(fNodes.map(n => n.id));
        const fEdges = graphData.edges.filter(e => activeEdgeTypes[e.type.id] && fNodeIds.has(e.source) && fNodeIds.has(e.target));

        const d3Nodes: D3Node[] = fNodes.map(n => ({ ...n, x: 0, y: 0 }));
        const nMap = new Map(d3Nodes.map(n => [n.id, n]));
        const d3Links: D3Edge[] = fEdges.map(e => ({ source: nMap.get(e.source)!, target: nMap.get(e.target)!, type: e.type }));

        const cx = d3.mean(graphData.nodes, n => n.jsonX) || 0;
        const cy = d3.mean(graphData.nodes, n => n.jsonY) || 0;
        const cz = d3.mean(graphData.nodes, n => n.jsonZ) || 0;
        const viewScale = Math.min(width, height) * 0.04;

        const link = g.append("g").selectAll("line").data(d3Links).join("line")
            .attr("stroke", d => d.type.color).attr("stroke-width", d => d.type.width).attr("stroke-dasharray", d => d.type.dash).attr("opacity", 0.6);

        const nodeGroup = g.append("g").selectAll("g").data(d3Nodes).join("g")
            .on("mouseover", (_, d) => setHovered(d)).on("mouseout", () => setHovered(null));

        nodeGroup.each(function(d) {
            const el = d3.select(this);
            const m = d.type;
            if (m.shape === "circle") el.append("circle").attr("r", m.r).attr("fill", m.color + "66").attr("stroke", m.color).attr("stroke-width", 2);
            else if (m.shape === "rect") el.append("rect").attr("width", m.r*2).attr("height", m.r*1.5).attr("x", -m.r).attr("y", -m.r*0.75).attr("fill", m.color + "66").attr("stroke", m.color).attr("stroke-width", 2);
            else if (m.shape === "diamond") el.append("path").attr("d", `M 0 ${-m.r} L ${m.r} 0 L 0 ${m.r} L ${-m.r} 0 Z`).attr("fill", m.color + "66").attr("stroke", m.color).attr("stroke-width", 2);
            else el.append("path").attr("d", `M 0 ${-m.r} L ${m.r*0.9} ${-m.r*0.5} L ${m.r*0.9} ${m.r*0.5} L 0 ${m.r} L ${-m.r*0.9} ${m.r*0.5} L ${-m.r*0.9} ${-m.r*0.5} Z`).attr("fill", m.color + "66").attr("stroke", m.color).attr("stroke-width", 2);

            if (mode === "forecast" && riskProbs[d.id] && !repairedNodes.has(d.id)) {
                el.append("circle").attr("class", "pulse-ring").attr("r", m.r + 10).attr("fill", "none").attr("stroke", "#FF1744").attr("stroke-width", 3);
            }
        });

        const brigadeG = g.append("g").attr("display", mode === "forecast" ? "block" : "none");
        brigadeG.append("circle").attr("r", 16).attr("fill", "#FFD700").attr("stroke", "#000").attr("stroke-width", 1.5);
        brigadeG.append("text").attr("font-size", "18").attr("text-anchor", "middle").attr("dy", "6").text("🛠️");

        const update = () => {
            d3Nodes.forEach(d => {
                const p = project3D(d.jsonX, d.jsonY, d.jsonZ, cx, cy, cz, viewScale, rotXRef.current, rotYRef.current);
                d.x = width / 2 + p.sx; d.y = height / 2 + p.sy;
            });
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            nodeGroup.attr("transform", d => `translate(${d.x},${d.y})`);
            if (brigade3DRef.current) {
                const p = project3D(brigade3DRef.current.jsonX, brigade3DRef.current.jsonY, brigade3DRef.current.jsonZ, cx, cy, cz, viewScale, rotXRef.current, rotYRef.current);
                brigadeG.attr("transform", `translate(${width/2 + p.sx}, ${height/2 + p.sy})`);
            }
        };

        const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.1, 10])
            .filter((e) => e.type === 'wheel' || (e.type === 'mousedown' && e.button === 2))
            .on("zoom", (e) => g.attr("transform", e.transform));

        const drag = d3.drag<SVGSVGElement, unknown>().filter((e) => e.button === 0)
            .on("drag", (e) => {
                rotYRef.current += e.dx * 0.5;
                rotXRef.current = Math.max(-85, Math.min(85, rotXRef.current + e.dy * 0.5));
                update();
            });

        svg.call(zoom as any).call(drag as any);
        zoomRef.current = zoom;

        let raf: number;
        const tick = () => { if (isAutoRotating) { rotYRef.current += 0.5; update(); } raf = requestAnimationFrame(tick); };
        tick(); update();
        return () => cancelAnimationFrame(raf);
    }, [graphData, activeNodeTypes, activeEdgeTypes, loading, mode, isAutoRotating, riskProbs, repairedNodes]);

    // Переключение в режим прогноза с генерацией случайных аварийных узлов
    const handleForecastMode = () => {
        setMode('forecast');
        setRepairedNodes(new Set()); // Сброс прошлых ремонтов

        if (graphData.nodes.length > 0) {
            // Исключаем TECH и ITP из возможных аварий, выбираем случайные узлы (например, APT, RISER или LIFT)
            const potentialTargets = graphData.nodes.filter(n => n.type.id !== "TECH" && n.type.id !== "ITP");

            // Выбираем 2-3 случайных узла для симуляции аварии
            const shuffled = [...potentialTargets].sort(() => 0.5 - Math.random());
            const selectedNodes = shuffled.slice(0, Math.min(3, shuffled.length));

            const newRisks: Record<string, number> = {};
            selectedNodes.forEach(n => {
                newRisks[n.id] = parseFloat((0.6 + Math.random() * 0.3).toFixed(2));
            });
            setRiskProbs(newRisks);

            // Сбрасываем позицию бригады в начальное тех. помещение
            const startNode = graphData.nodes.find(n => n.type.id === "TECH") || graphData.nodes[0];
            if (startNode) {
                brigade3DRef.current = { jsonX: startNode.jsonX, jsonY: startNode.jsonY, jsonZ: startNode.jsonZ };
            }
        }
    };

    // Симуляция движения бригады к авариям и возврат назад
    const runSimulation = async () => {
        if (isSimulating) return;
        setIsSimulating(true);

        const startNode = graphData.nodes.find(n => n.type.id === "TECH") || graphData.nodes[0];
        const targets = Object.keys(riskProbs);

        let currentNodePosition = { jsonX: startNode.jsonX, jsonY: startNode.jsonY, jsonZ: startNode.jsonZ };

        // 1. Едем по всем точкам аварий последовательно
        for (const targetId of targets) {
            const tNode = graphData.nodes.find(n => n.id === targetId)!;
            if (!tNode) continue;

            for (let s = 0; s <= 30; s++) {
                const t = s / 30;
                brigade3DRef.current = {
                    jsonX: currentNodePosition.jsonX + (tNode.jsonX - currentNodePosition.jsonX) * t,
                    jsonY: currentNodePosition.jsonY + (tNode.jsonY - currentNodePosition.jsonY) * t,
                    jsonZ: currentNodePosition.jsonZ + (tNode.jsonZ - currentNodePosition.jsonZ) * t
                };
                await new Promise(r => setTimeout(r, 20));
            }

            // Фиксируем устранение аварии в узле
            setRepairedNodes(prev => {
                const next = new Set<string>(prev);
                next.add(targetId);
                return next;
            });

            currentNodePosition = { jsonX: tNode.jsonX, jsonY: tNode.jsonY, jsonZ: tNode.jsonZ };
            await new Promise(r => setTimeout(r, 400));
        }

        // 2. Возвращаемся обратно в исходную точку (TECH)
        for (let s = 0; s <= 30; s++) {
            const t = s / 30;
            brigade3DRef.current = {
                jsonX: currentNodePosition.jsonX + (startNode.jsonX - currentNodePosition.jsonX) * t,
                jsonY: currentNodePosition.jsonY + (startNode.jsonY - currentNodePosition.jsonY) * t,
                jsonZ: currentNodePosition.jsonZ + (startNode.jsonZ - currentNodePosition.jsonZ) * t
            };
            await new Promise(r => setTimeout(r, 20));
        }

        setIsSimulating(false);
    };

    return (
        <div style={st.container}>
            <div style={st.sidebar}>
                <div style={st.header}>УК ГРАФ</div>

                {/* Восстановленный блок параметров дома из BuildingGraph_1.tsx */}
                <div style={{ padding: "0 0 20px 0", borderBottom: "1px solid #41618a", marginBottom: 20 }}>
                    <div style={{ color: "#7EB8D4", fontSize: "11px", fontWeight: "bold", marginBottom: 12, textTransform: "uppercase", letterSpacing: "1px" }}>ПАРАМЕТРЫ ДОМА</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}><span>Этажей</span><span style={{ color: "#4A9EFF", fontWeight: "bold" }}>{buildingParams.floors}</span></div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}><span>Секций</span><span style={{ color: "#4A9EFF", fontWeight: "bold" }}>{buildingParams.sections}</span></div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}><span>Кв/этаж</span><span style={{ color: "#4A9EFF", fontWeight: "bold" }}>{buildingParams.aptsPerFloor}</span></div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}><span>Лифтов/секц</span><span style={{ color: "#4A9EFF", fontWeight: "bold" }}>{buildingParams.liftsPerSection}</span></div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}><span>Стояков/секц</span><span style={{ color: "#4A9EFF", fontWeight: "bold" }}>{buildingParams.risersPerSection}</span></div>
                </div>

                <div style={st.section}>
                    <div style={st.secTitle}>УЗЛЫ</div>
                    {Object.entries(NODE_TYPES).map(([k, v]) => (
                        <div key={k} onClick={() => setActiveNodeTypes(p => ({...p, [k]: !p[k]}))} style={{...st.item, opacity: activeNodeTypes[k] ? 1 : 0.3}}>
                            <div style={{...st.dot, background: v.color}} /> {v.label}
                        </div>
                    ))}
                </div>

                <div style={st.section}>
                    <div style={st.secTitle}>СВЯЗИ</div>
                    {Object.entries(EDGE_TYPES).map(([k, v]) => (
                        <div key={k} onClick={() => setActiveEdgeTypes(p => ({...p, [k]: !p[k]}))} style={{...st.item, opacity: activeEdgeTypes[k] ? 1 : 0.3}}>
                            <div style={{width: 15, height: 2, background: v.color, marginRight: 8}} /> {v.label}
                        </div>
                    ))}
                </div>
            </div>

            <div style={st.main}>
                <div style={st.topBar}>
                    <div style={st.modeSwitch}>
                        <button onClick={() => setMode('original')} style={{...st.mBtn, background: mode === 'original' ? '#4A9EFF' : 'transparent'}}>ГРАФ</button>
                        <button onClick={handleForecastMode} style={{...st.mBtn, background: mode === 'forecast' ? '#FF1744' : 'transparent'}}>ПРОГНОЗ</button>
                    </div>
                    <div style={st.controls}>
                        <button onClick={() => zoomRef.current && d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 1.5)} style={st.ctrlBtn}>➕</button>
                        <button onClick={() => zoomRef.current && d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 0.7)} style={st.ctrlBtn}>➖</button>
                        <button onClick={() => setIsAutoRotating(!isAutoRotating)} style={st.ctrlBtn}>{isAutoRotating ? "⏸" : "▶️"}</button>
                        {mode === 'forecast' && <button onClick={runSimulation} style={st.dangerBtn} disabled={isSimulating}>🚨 БРИГАДА</button>}
                    </div>
                </div>
                <svg ref={svgRef} style={{flex: 1, background: "#060D14"}} />
                {hovered && <div style={st.tooltip}><b>{hovered.label}</b><br/>Этаж: {hovered.floor}</div>}
            </div>
            <style>{`
                @keyframes pulse { 0%, 100% { opacity: 0.9; } 50% { opacity: 0.2; } }
                .pulse-ring { animation: pulse 1.5s infinite; transform-origin: center; }
            `}</style>
        </div>
    );
}

const st: Record<string, React.CSSProperties> = {
    container: { display: "flex", height: "100vh", background: "#060D14", color: "#fff", fontFamily: "sans-serif" },
    sidebar: { width: 220, background: "#132133", padding: 20, borderRight: "1px solid #41618a", overflowY: "auto" },
    main: { flex: 1, display: "flex", flexDirection: "column", position: "relative" },
    header: { fontSize: 20, fontWeight: "bold", color: "#4A9EFF", marginBottom: 25 },
    section: { marginBottom: 30 },
    secTitle: { fontSize: 11, color: "#7EB8D4", marginBottom: 12, textTransform: "uppercase", letterSpacing: "1px" },
    item: { display: "flex", alignItems: "center", marginBottom: 10, cursor: "pointer", fontSize: 13 },
    dot: { width: 10, height: 10, borderRadius: 2, marginRight: 8 },
    topBar: { height: 65, background: "#132133", display: "flex", alignItems: "center", padding: "0 20px", justifyContent: "space-between" },
    modeSwitch: { display: "flex", background: "#060D14", borderRadius: 8, padding: 4 },
    mBtn: { border: "none", padding: "6px 15px", borderRadius: 6, color: "#fff", cursor: "pointer", fontSize: 12 },
    controls: { display: "flex", gap: 10 },
    ctrlBtn: { background: "#1E3A54", border: "none", color: "#fff", width: 35, height: 35, borderRadius: 6, cursor: "pointer" },
    dangerBtn: { background: "#FF1744", border: "none", color: "#fff", padding: "0 15px", borderRadius: 6, cursor: "pointer", fontWeight: "bold" },
    tooltip: { position: "absolute", bottom: 20, right: 20, background: "#132133", padding: 15, borderRadius: 10, border: "1px solid #4A9EFF" }
};