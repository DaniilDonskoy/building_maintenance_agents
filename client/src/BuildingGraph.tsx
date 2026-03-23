import React, { useState, useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";

const JSON_PATH = "/house_graph_example.json";

// ====================== ИНТЕРФЕЙСЫ ======================
interface D3Node extends GraphNode, d3.SimulationNodeDatum {}

interface D3Edge extends d3.SimulationLinkDatum<D3Node> {
  type: EdgeType;
}

type LayoutMode = "force" | "layered" | "isometric";

export interface NodeTypeConfig {
  label: string;
  color: string;
  shape: 'circle' | 'rect' | 'diamond' | 'hexagon';
  r: number;
  layer: string;
}

export interface EdgeTypeConfig {
  label: string;
  color: string;
  dash: string;
  width: number;
}

export interface NodeParams {
  label?: string;
  layer?: number;
  section?: number;
  floor?: number;
}

// ====================== КЛАССЫ ======================
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
  public jsonY: number = 0;   // ← добавлено
  public jsonZ: number = 0;

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
  constructor(
    public source: string,
    public target: string,
    public type: EdgeType
  ) {}
}

// ====================== ТИПЫ ======================
export const NODE_TYPES: Record<string, NodeType> = {
  APT:   new NodeType("APT",   { label: "Квартира", color: "#4A9EFF", shape: "rect", r: 10, layer: "floor" }),
  MOP:   new NodeType("MOP",   { label: "МОП", color: "#22D3A0", shape: "rect", r: 12, layer: "floor" }),
  LIFT:  new NodeType("LIFT",  { label: "Лифт", color: "#F5A623", shape: "circle", r: 10, layer: "floor" }),
  RISER: new NodeType("RISER", { label: "Стояк", color: "#B06AFF", shape: "diamond", r: 9, layer: "vertical" }),
  PANEL: new NodeType("PANEL", { label: "Эл. щит", color: "#FF6B6B", shape: "hexagon", r: 11, layer: "tech" }),
  ITP:   new NodeType("ITP",   { label: "ИТП", color: "#FF9F43", shape: "hexagon", r: 14, layer: "basement" }),
  TECH:  new NodeType("TECH",  { label: "Тех. помещение", color: "#54A0FF", shape: "rect", r: 13, layer: "basement" }),
  ROOF:  new NodeType("ROOF",  { label: "Тех. этаж/кровля", color: "#A29BFE", shape: "rect", r: 13, layer: "roof" }),
};

export const EDGE_TYPES: Record<string, EdgeType> = {
  ADJ:   new EdgeType("ADJ",   { label: "Смежность", color: "#4A9EFF44", dash: "", width: 1.5 }),
  HEAT:  new EdgeType("HEAT",  { label: "Теплоснабжение", color: "#FF6B6BCC", dash: "6,3", width: 2 }),
  COLD:  new EdgeType("COLD",  { label: "Хол. водоснабжение", color: "#4A9EFFCC", dash: "6,3", width: 2 }),
  HOT:   new EdgeType("HOT",   { label: "Гор. водоснабжение", color: "#FF9F43CC", dash: "6,3", width: 2 }),
  ELEC:  new EdgeType("ELEC",  { label: "Электроснабжение", color: "#FFD32ACC", dash: "4,2", width: 2 }),
  VENT:  new EdgeType("VENT",  { label: "Вентиляция", color: "#22D3A0AA", dash: "8,4", width: 1.5 }),
  DRAIN: new EdgeType("DRAIN", { label: "Канализация", color: "#A29BFEAA", dash: "3,3", width: 1.5 }),
};

const NODE_TYPE_MAPPING: Record<string, NodeType> = {
  TechNode: NODE_TYPES.ITP,
  ElecNode: NODE_TYPES.PANEL,
  MopNode:  NODE_TYPES.MOP,
  ElevNode: NODE_TYPES.LIFT,
  FlatNode: NODE_TYPES.APT,
  RiserNode: NODE_TYPES.RISER,
};

function getNodeLabel(jn: any): string {
  const f = jn.features || {};
  switch (jn.type) {
    case "FlatNode":  return `КВ.${f.flat_index ?? ""} (Э.${f.floor ?? ""})`;
    case "MopNode":   return `ХОЛЛ С.${f.section ?? ""} ЭТ.${f.floor ?? ""}`;
    case "ElevNode":  return `ЛИФТ ${f.elev_index ?? 1}`;
    case "RiserNode": return `СТ.${f.flat_index ?? ""}`;
    case "ElecNode":  return `ЩЭ-${f.floor ?? ""}.${f.section ?? ""}`;
    case "TechNode":  return "ЦЕНТРАЛЬНЫЙ ИТП";
    default:          return jn.type || "Узел";
  }
}

function getNodeParams(jn: any): NodeParams {
  const f = jn.features || {};
  return {
    label: getNodeLabel(jn),
    layer: f.floor ?? f.z ?? 0,
    section: typeof f.section === "number" ? f.section : -1,
    floor: f.floor ?? 0,
  };
}

function getEdgeType(je: any): EdgeType {
  if (je.type === "PathEdge") return EDGE_TYPES.ADJ;
  const f = je.features || {};
  if (f.vertical === 1 && f.horizontal === 0) return EDGE_TYPES.VENT;
  if (f.vertical === 0 && f.horizontal === 1) return EDGE_TYPES.ELEC;
  if (f.oriented === 1) return EDGE_TYPES.HEAT;
  return EDGE_TYPES.COLD;
}

function parseBuildingGraph(json: any): BuildingGraph {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  json.nodes?.forEach((jn: any) => {
    const nodeType = NODE_TYPE_MAPPING[jn.type] || NODE_TYPES.TECH;
    const node = new GraphNode(String(jn.id), nodeType, getNodeParams(jn));
    const f = jn.features || {};
    node.jsonX = f.x ?? 0;
    node.jsonY = f.y ?? 0;   // ← используем y
    node.jsonZ = f.z ?? 0;
    nodes.push(node);
  });

  json.edges?.forEach((je: any) => {
    edges.push(new GraphEdge(String(je.source), String(je.target), getEdgeType(je)));
  });

  return { nodes, edges };
}

interface BuildingGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ====================== ИЗОМЕТРИЧЕСКАЯ ПРОЕКЦИЯ ======================
function projectIsometric(x: number, y: number, z: number) {
  const sx = (x - y) * 0.85;
  const sy = (x + y) * 0.42 - z * 0.72;
  return { sx, sy };
}

// ====================== ОСНОВНОЙ КОМПОНЕНТ ======================
export default function BuildingGraph() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simRef = useRef<d3.Simulation<D3Node, D3Edge> | null>(null);

  const [graphData, setGraphData] = useState<BuildingGraph>({ nodes: [], edges: [] });
  const [activeEdgeTypes, setActiveEdgeTypes] = useState<Record<string, boolean>>(
    Object.fromEntries(Object.keys(EDGE_TYPES).map(k => [k, true]))
  );
  const [activeNodeTypes, setActiveNodeTypes] = useState<Record<string, boolean>>(
    Object.fromEntries(Object.keys(NODE_TYPES).map(k => [k, true]))
  );

  const [layoutMode, setLayoutMode] = useState<LayoutMode>("isometric");
  const [hovered, setHovered] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [buildingParams, setBuildingParams] = useState({
    floors: 0, sections: 0, aptsPerFloor: 0, liftsPerSection: 0, risersPerSection: 0,
  });

  // Загрузка JSON
  useEffect(() => {
    fetch(JSON_PATH)
      .then(res => res.ok ? res.json() : Promise.reject(`HTTP ${res.status}`))
      .then(data => {
        const parsed = parseBuildingGraph(data);
        setGraphData(parsed);

        const floorsSet = new Set<number>();
        const sectionsSet = new Set<number>();
        let liftCount = 0, riserCount = 0, aptCount = 0;

        parsed.nodes.forEach(node => {
          if (node.floor > 0) floorsSet.add(node.floor);
          if (node.section >= 0) sectionsSet.add(node.section);
          if (node.type.id === "LIFT") liftCount++;
          if (node.type.id === "RISER") riserCount++;
          if (node.type.id === "APT") aptCount++;
        });

        const floors = floorsSet.size || 1;
        const sections = sectionsSet.size || 1;

        setBuildingParams({
          floors,
          sections,
          aptsPerFloor: Math.round(aptCount / (floors * sections)) || 3,
          liftsPerSection: Math.ceil(liftCount / sections),
          risersPerSection: Math.ceil(riserCount / sections),
        });

        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError("Не удалось загрузить house_graph_example.json");
        setLoading(false);
      });
  }, []);

  const stats = useMemo(() => ({
    nodes: graphData.nodes.length,
    edges: graphData.edges.length,
  }), [graphData]);

  // ====================== D3 ВИЗУАЛИЗАЦИЯ ======================
  useEffect(() => {
    if (loading || error || !graphData.nodes.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    const W = svgRef.current.clientWidth || 900;
    const H = svgRef.current.clientHeight || 640;

    const filteredNodes = graphData.nodes.filter(n => activeNodeTypes[n.type.id]);
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = graphData.edges.filter(e =>
      activeEdgeTypes[e.type.id] && nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    const nodes: D3Node[] = filteredNodes.map(n => ({ ...n } as D3Node));
    const links: D3Edge[] = filteredEdges.map(e => ({ ...e } as D3Edge));

    // === ИЗОМЕТРИЧЕСКАЯ ПРОЕКЦИЯ с x, y, z ===
    nodes.forEach(d => {
      const p = projectIsometric(d.jsonX, d.jsonY, d.jsonZ);
      d.x = p.sx;
      d.y = p.sy;
    });

    // Центрирование
    const minX = Math.min(...nodes.map(d => d.x!));
    const maxX = Math.max(...nodes.map(d => d.x!));
    const minY = Math.min(...nodes.map(d => d.y!));
    const maxY = Math.max(...nodes.map(d => d.y!));

    const scale = Math.min(W * 0.82 / (maxX - minX), H * 0.82 / (maxY - minY));
    const offsetX = W / 2 - (minX + maxX) / 2 * scale;
    const offsetY = H / 2 - (minY + maxY) / 2 * scale;

    nodes.forEach(d => {
      d.x = offsetX + d.x! * scale;
      d.y = offsetY + d.y! * scale;
    });

    const link = g.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", d => d.type.color)
      .attr("stroke-width", d => d.type.width)
      .attr("stroke-dasharray", d => d.type.dash)
      .attr("opacity", 0.4);

    const nodeG = g.append("g")
      .selectAll<SVGGElement, D3Node>("g")
      .data(nodes)
      .join("g")
      .on("mouseover", (_, d) => setHovered(d))
      .on("mouseout", () => setHovered(null))
      .call(d3.drag<SVGGElement, D3Node>()
        .on("start", (event, d) => {
          if (!event.active) simRef.current?.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => {
          if (!event.active) simRef.current?.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );

    nodeG.each(function (d) {
      const el = d3.select(this);
      const m = d.type;
      const fill = m.color + "33";
      const stroke = m.color;

      if (m.shape === "rect") {
        el.append("rect")
          .attr("x", -m.r).attr("y", -m.r / 1.5)
          .attr("width", m.r * 2).attr("height", m.r * 1.3)
          .attr("rx", 2).attr("fill", fill).attr("stroke", stroke);
      } else if (m.shape === "diamond") {
        const size = m.r * 1.4;
        el.append("polygon")
          .attr("points", `0,${-size} ${size},0 0,${size} -${size},0`)
          .attr("fill", fill).attr("stroke", stroke);
      } else if (m.shape === "hexagon") {
        const pts: string[] = [];
        const r = m.r * 1.15;
        for (let i = 0; i < 6; i++) {
          const ang = (i * Math.PI) / 3 - Math.PI / 2;
          pts.push(`${(r * Math.cos(ang)).toFixed(2)},${(r * Math.sin(ang)).toFixed(2)}`);
        }
        el.append("polygon").attr("points", pts.join(" ")).attr("fill", fill).attr("stroke", stroke);
      } else {
        el.append("circle").attr("r", m.r).attr("fill", fill).attr("stroke", stroke);
      }
    });

    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force("link", d3.forceLink<D3Node, D3Edge>(links).id(d => d.id).distance(40))
      .force("charge", d3.forceManyBody().strength(-150))
      .force("x", d3.forceX(W / 2).strength(0.02))
      .force("y", d3.forceY(d => d.y!).strength(0.02))
      .on("tick", () => {
        link
          .attr("x1", d => (d.source as D3Node).x!)
          .attr("y1", d => (d.source as D3Node).y!)
          .attr("x2", d => (d.target as D3Node).x!)
          .attr("y2", d => (d.target as D3Node).y!);
        nodeG.attr("transform", d => `translate(${d.x || 0},${d.y || 0})`);
      });

    simRef.current = simulation;

    // ====================== ЗУМ + ПАНОРАМИРОВАНИЕ ======================
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoomBehavior);

    // Начальный вид
    const initialScale = 0.65;
    svg.call(zoomBehavior.transform, d3.zoomIdentity.scale(initialScale));

    return () => {
      simulation.stop();
    };
  }, [graphData, activeEdgeTypes, activeNodeTypes, layoutMode, loading, error]);

  if (loading) return <div style={{ padding: 40, color: "#7EB8D4" }}>Загрузка графа...</div>;
  if (error) return <div style={{ padding: 40, color: "#ff6666" }}>{error}</div>;

  return (
    <div style={{ display: "flex", height: "100vh", background: "#060D14", color: "#7EB8D4", fontFamily: "'Inter', sans-serif", fontSize: "12px" }}>
      
      {/* ЛЕВАЯ ПАНЕЛЬ — полностью как в твоём любимом коде */}
      <div style={{ width: "240px", flexShrink: 0, background: "#132133", borderRight: "1px solid #41618a", overflowY: "auto" }}>
        <div style={{ padding: "16px 14px 10px", borderBottom: "1px solid #0F2030" }}>
          <div style={{ color: "#4A9EFF", fontSize: "20px", fontWeight: "bold" }}>УК ГРАФ</div>
          <div style={{ color: "#FFFFFF", fontSize: "14px" }}>модель из JSON</div>
        </div>

        <div style={{ padding: "12px 14px", borderBottom: "1px solid #FFFFFF" }}>
          <div style={{ color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", marginBottom: 8 }}>ПАРАМЕТРЫ ДОМА</div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Этажей</span><span style={{ color: "#4A9EFF" }}>{buildingParams.floors}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Секций</span><span style={{ color: "#4A9EFF" }}>{buildingParams.sections}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Кв/этаж</span><span style={{ color: "#4A9EFF" }}>{buildingParams.aptsPerFloor}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Лифтов/секц</span><span style={{ color: "#4A9EFF" }}>{buildingParams.liftsPerSection}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between" }}><span>Стояков/секц</span><span style={{ color: "#4A9EFF" }}>{buildingParams.risersPerSection}</span></div>
        </div>

        <div style={{ padding: "10px 14px", borderBottom: "1px solid #FFFFFF" }}>
          <div style={{ color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", marginBottom: 12 }}>РАСКЛАДКА</div>
          {(["layered", "force", "isometric"] as LayoutMode[]).map(m => (
            <button key={m} onClick={() => setLayoutMode(m)} style={{
              display: "block", width: "100%", marginBottom: 4, padding: "5px",
              background: layoutMode === m ? "#52677D" : "transparent",
              border: "1px solid #52677D", color: layoutMode === m ? "#D1CFC9" : "#BDC4D4",
              borderRadius: 3, cursor: "pointer", fontSize: 11
            }}>
              {m === "isometric" ? "◆ Изометрия 3D" : m === "layered" ? "▶ Послойный (этажи)" : "◎ Force-directed"}
            </button>
          ))}
        </div>

        <div style={{ padding: "10px 14px", borderBottom: "1px solid #FFFFFF" }}>
          <div style={{ color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", marginBottom: 8 }}>УЗЛЫ</div>
          {Object.entries(NODE_TYPES).map(([k, v]) => (
            <div key={k}
              onClick={() => setActiveNodeTypes(p => ({ ...p, [k]: !p[k] }))}
              style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5, cursor: "pointer", opacity: activeNodeTypes[k] ? 1 : 0.35 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: v.color }} />
              <span style={{ color: "#FFFFFF" }}>{v.label}</span>
            </div>
          ))}
        </div>

        <div style={{ padding: "10px 14px" }}>
          <div style={{ color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", marginBottom: 8 }}>СВЯЗИ</div>
          {Object.entries(EDGE_TYPES).map(([k, v]) => (
            <div key={k}
              onClick={() => setActiveEdgeTypes(p => ({ ...p, [k]: !p[k] }))}
              style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5, cursor: "pointer", opacity: activeEdgeTypes[k] ? 1 : 0.35 }}>
              <svg width="20" height="8">
                <line x1="0" y1="4" x2="20" y2="4" stroke={v.color.slice(0,7)} strokeWidth={v.width} strokeDasharray={v.dash} />
              </svg>
              <span style={{ color: "#FFFFFF" }}>{v.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Основная область */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
        <div style={{ height: "36px", background: "#132133", borderBottom: "1px solid #41618a", display: "flex", alignItems: "center", padding: "0 16px", gap: 24 }}>
          <span>Узлов: <span style={{ color: "#4A9EFF" }}>{stats.nodes}</span></span>
          <span>Рёбер: <span style={{ color: "#4A9EFF" }}>{stats.edges}</span></span>
          <span style={{ marginLeft: "auto", fontSize: "11px", color: "#88CCFF" }}>
            Колёсико мыши — зум. Зажать + двигать — перемещение графа
          </span>
        </div>

        <svg
          ref={svgRef}
          style={{ flex: 1, background: "#060D14", cursor: "grab" }}
        />

        {hovered && (
          <div style={{
            position: "absolute", bottom: 16, right: 16,
            background: "#0A1824", border: "1px solid #1E3A54",
            padding: "10px 14px", borderRadius: 6, minWidth: 200
          }}>
            <div style={{ color: hovered.type.color, fontSize: "11px" }}>{hovered.type.label}</div>
            <div style={{ color: "#FFFFFF", fontSize: "14px" }}>{hovered.label}</div>
            {hovered.floor > 0 && <div>Этаж: {hovered.floor}</div>}
            {hovered.section >= 0 && <div>Секция: {hovered.section + 1}</div>}
            <div style={{ fontSize: "12px", opacity: 0.8 }}>
              x: {hovered.jsonX.toFixed(1)} | 
              y: {hovered.jsonY.toFixed(1)} | 
              z: {hovered.jsonZ.toFixed(1)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}