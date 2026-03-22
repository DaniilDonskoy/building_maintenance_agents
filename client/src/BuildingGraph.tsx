import React, {useState, useEffect, useRef, useMemo, CSSProperties} from "react";
import * as d3 from "d3";

interface D3Node extends GraphNode, d3.SimulationNodeDatum {}

interface D3Edge extends d3.SimulationLinkDatum<D3Node> {
  type: EdgeType;
  source: string | D3Node;
  target: string | D3Node;
}

type LayoutMode = "force" | "layered";

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

export interface NodeParams {
  label?: string;
  layer?: number;
  section?: number;
  floor?: number;
}

export class GraphNode {
  public id: string;
  public type: NodeType;
  public label: string;
  public layer: number;
  public section: number;
  public floor: number;

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

interface GraphConfig {
  floors: number;
  sections: number;
  aptsPerFloor: number;
  liftsPerSection: number;
  risersPerSection: number;
}

interface BuildingGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

function generateBuildingGraph(config: GraphConfig): BuildingGraph {
  const { floors, sections, aptsPerFloor, liftsPerSection, risersPerSection } = config;
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const idMap = new Map<string, GraphNode>();

  const addNode = (id: string, typeObj: NodeType, params: NodeParams): GraphNode => {
    const node = new GraphNode(id, typeObj, params);
    nodes.push(node);
    idMap.set(id, node);
    return node;
  };

  const itp = addNode("itp", NODE_TYPES.ITP, { label: "ЦЕНТРАЛЬНЫЙ ИТП", layer: 0 });
  const tech = addNode("tech_base", NODE_TYPES.TECH, { label: "ТЕХ. ПОДПОЛЬЕ", layer: 0 });
  const grsh = addNode("grsh_main", NODE_TYPES.PANEL, { label: "ГРЩ ЗДАНИЯ", layer: 0 });

  edges.push(new GraphEdge(itp.id, tech.id, EDGE_TYPES.ADJ));

  const lastRisers: Record<string, string> = {};

  for (let f = 1; f <= floors; f++) {
    for (let s = 0; s < sections; s++) {
      const sectionPrefix = `S${s+1}_F${f}`;

      const mop = addNode(`mop_${sectionPrefix}`, NODE_TYPES.MOP, {
        label: `ХОЛЛ С.${s+1} ЭТ.${f}`,
        layer: f, section: s, floor: f
      });

      for (let l = 0; l < liftsPerSection; l++) {
        const lift = addNode(`lift_${sectionPrefix}_${l}`, NODE_TYPES.LIFT, {
          label: `ЛИФТ ${l+1}`, layer: f, section: s
        });
        edges.push(new GraphEdge(mop.id, lift.id, EDGE_TYPES.ADJ));
      }

      const panel = addNode(`panel_${sectionPrefix}`, NODE_TYPES.PANEL, {
        label: `ЩЭ-${f}.${s+1}`, layer: f, section: s
      });
      edges.push(new GraphEdge(mop.id, panel.id, EDGE_TYPES.ADJ));
      edges.push(new GraphEdge(grsh.id, panel.id, EDGE_TYPES.ELEC));

      const systems = [
        { key: 'HEAT', type: NODE_TYPES.RISER, edge: EDGE_TYPES.HEAT, lab: 'ОТП' },
        { key: 'COLD', type: NODE_TYPES.RISER, edge: EDGE_TYPES.COLD, lab: 'ХВС' },
        { key: 'HOT',  type: NODE_TYPES.RISER, edge: EDGE_TYPES.HOT,  lab: 'ГВС' },
        { key: 'DRAIN',type: NODE_TYPES.RISER, edge: EDGE_TYPES.DRAIN,lab: 'КАН' }
      ];

      systems.forEach(sys => {
        const rNode = addNode(`riser_${sys.key}_${s}_${f}`, sys.type, {
          label: `СТ.${sys.lab}`, layer: f, section: s
        });

        edges.push(new GraphEdge(mop.id, rNode.id, EDGE_TYPES.ADJ));

        const prevKey = `${sys.key}_${s}`;
        if (f === 1) {
          edges.push(new GraphEdge(itp.id, rNode.id, sys.edge));
        } else if (lastRisers[prevKey]) {
          edges.push(new GraphEdge(lastRisers[prevKey], rNode.id, sys.edge));
        }
        lastRisers[prevKey] = rNode.id;

        const aptsThisRiser = Math.ceil(aptsPerFloor / risersPerSection);
        for (let a = 0; a < aptsThisRiser; a++) {
          const aptId = `apt_${sectionPrefix}_r${sys.key}_a${a}`;
          addNode(aptId, NODE_TYPES.APT, {
            label: `КВ.${a+1} (Э.${f})`, layer: f, section: s
          });
          edges.push(new GraphEdge(rNode.id, aptId, sys.edge));
          edges.push(new GraphEdge(mop.id, aptId, EDGE_TYPES.ADJ));
          edges.push(new GraphEdge(panel.id, aptId, EDGE_TYPES.ELEC));
        }
      });
    }
  }

  addNode("roof", NODE_TYPES.ROOF, { label: "КРОВЛЯ / ТЕХ. ЭТАЖ", layer: floors + 1 });

  return { nodes, edges };
}

export default function BuildingGraph() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simRef = useRef<d3.Simulation<D3Node, D3Edge> | null>(null);

  const [params, setParams] = useState<GraphConfig>({
    floors: 5, sections: 2, aptsPerFloor: 4, liftsPerSection: 1, risersPerSection: 1,
  });

  const setParam = (k: keyof GraphConfig, v: number) => {
    const limits: Record<keyof GraphConfig, number> = {
      floors: 25, sections: 5, aptsPerFloor: 12, liftsPerSection: 3, risersPerSection: 4
    };
    const val = Math.max(1, Math.min(v, limits[k] || 10));
    setParams(p => ({ ...p, [k]: val }));
  };

  const [activeEdgeTypes, setActiveEdgeTypes] = useState<Record<string, boolean>>(
    Object.fromEntries(Object.keys(EDGE_TYPES).map(k => [k, true]))
  );
  const [activeNodeTypes, setActiveNodeTypes] = useState<Record<string, boolean>>(
    Object.fromEntries(Object.keys(NODE_TYPES).map(k => [k, true]))
  );

  const [layoutMode, setLayoutMode] = useState<LayoutMode>("layered");
  const [graphData, setGraphData] = useState<BuildingGraph>({ nodes: [], edges: [] });
  const [hovered, setHovered] = useState<GraphNode | null>(null);

  useEffect(() => {
    setGraphData(generateBuildingGraph(params));
  }, [params]);

  const stats = useMemo(() => ({
    nodes: graphData.nodes.length,
    edges: graphData.edges.length,
  }), [graphData]);

  const inputStyle: CSSProperties = {
    background: "#0D1B2A",
    border: "1px solid #1E3A54",
    color: "#7EB8D4",
    padding: "4px 8px",
    borderRadius: "4px",
    width: "45px",
    fontFamily: "monospace",
    outline: "none"
  };

  useEffect(() => {
    if (!graphData.nodes.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const container = svgRef.current;
    const W = container.clientWidth || 900;
    const H = container.clientHeight || 640;

    const filteredNodes = graphData.nodes.filter(n => activeNodeTypes[n.type.id]);
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = graphData.edges.filter(e =>
      activeEdgeTypes[e.type.id] && nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    const nodes: D3Node[] = filteredNodes.map(n => ({ ...n } as D3Node));
    const links: D3Edge[] = filteredEdges.map(e => ({ ...e } as D3Edge));

    const g = svg.append("g");
    const maxLayer = Math.max(...nodes.map(n => n.layer)) || 1;
    const layerH = H / (maxLayer + 2);

    const link = g.append("g")
      .selectAll<SVGLineElement, D3Edge>("line")
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
      .on("mouseover", (_e, d) => setHovered(d))
      .on("mouseout", () => setHovered(null))
      .call(d3.drag<SVGGElement, D3Node>()
        .on("start", (e, d) => {
          if (!e.active && simRef.current) simRef.current.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (e, d) => {
          d.fx = e.x;
          d.fy = e.y;
        })
        .on("end", (e, d) => {
          if (!e.active && simRef.current) simRef.current.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    nodeG.each(function(d) {
      const el = d3.select(this);
      const meta = d.type;
      if (meta.shape === "rect") {
        el.append("rect")
          .attr("x", -meta.r).attr("y", -meta.r / 1.5)
          .attr("width", meta.r * 2).attr("height", meta.r * 1.3)
          .attr("rx", 2).attr("fill", meta.color + "33").attr("stroke", meta.color);
      } else {
        el.append("circle")
          .attr("r", meta.r).attr("fill", meta.color + "33").attr("stroke", meta.color);
      }
    });

    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force("link", d3.forceLink<D3Node, D3Edge>(links).id(d => d.id).distance(40))
      .force("charge", d3.forceManyBody().strength(-150))
      .force("y", d3.forceY<D3Node>(d =>
        layoutMode === "layered" ? H - (d.layer + 1) * layerH : H / 2
      ).strength(1))
      .force("x", d3.forceX<D3Node>(W / 2).strength(0.1))
      .on("tick", () => {
        link
          .attr("x1", d => (d.source as D3Node).x!)
          .attr("y1", d => (d.source as D3Node).y!)
          .attr("x2", d => (d.target as D3Node).x!)
          .attr("y2", d => (d.target as D3Node).y!);

        nodeG.attr("transform", d => `translate(${d.x},${d.y})`);
      });

    simRef.current = simulation;

    return () => {
      simulation.stop();
    };
  }, [graphData, activeEdgeTypes, activeNodeTypes, layoutMode]);

  return (
    <div style={{
      display: "flex", height: "100vh", background: "#060D14", color: "#7EB8D4",
      fontFamily: "'Inter', 'Helvetica Neue', 'Arial', sans-serif",
      fontSize: "12px",
    }}>
      <div style={{
        width: "240px", flexShrink: 0, background: "#132133",
        borderRight: "1px solid #41618a", overflowY: "auto",
        display: "flex", flexDirection: "column", gap: "0",
      }}>
        <div style={{ padding: "16px 14px 10px", borderBottom: "1px solid #0F2030" }}>
          <div style={{ color: "#4A9EFF", fontSize: "20px", fontWeight: "bold", letterSpacing: "2px", marginBottom: 4 }}>УК ГРАФ</div>
          <div style={{ color: "#FFFFFF", fontSize: "14px" }}>параметрическая модель</div>
        </div>

        <div style={{ padding: "12px 14px", borderBottom: "1px solid #FFFFFF" }}>
          <div style={{ color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", letterSpacing: "1px", marginBottom: 8 }}>ПАРАМЕТРЫ</div>
          {(
            [
              ["floors", "Этажей"],
              ["sections", "Секций"],
              ["aptsPerFloor", "Кв/этаж/секц"],
              ["liftsPerSection", "Лифтов/секц"],
              ["risersPerSection", "Стояков/секц"],
            ] as [keyof GraphConfig, string][]
          ).map(([k, label]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ color: "#FFFFFF", fontSize: "14px" }}>{label}</span>
              <input
                type="number"
                value={params[k]}
                min={1}
                onChange={e => setParam(k, +e.target.value)}
                style={{
                  background: "#0F1A2B",
                  border: "1px solid #52677D",
                  color: "#BDC4D4",
                  fontFamily: "monospace",
                  fontSize: 11,
                  width: 60,
                  padding: "2px 4px"
                }}
              />
            </div>
          ))}
        </div>

        <div style={{padding: "10px 14px", borderBottom: "1px solid #FFFFFF"}}>
          <div style={{color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", letterSpacing: "1px", marginBottom: 12}}>РАСКЛАДКА</div>
          {(["layered", "force"] as LayoutMode[]).map(m => (
            <button key={m} onClick={() => setLayoutMode(m)} style={{
              display: "block",
              width: "100%",
              marginBottom: 4,
              padding: "5px",
              background: layoutMode === m ? "#52677D" : "transparent",
              border: `1px solid #52677D`,
              color: layoutMode === m ? "#D1CFC9" : "#BDC4D4",
              borderRadius: 3,
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 11,
              textAlign: "left",
            }}>
              {m === "layered" ? "▶ Послойный (этажи)" : "◎ Force-directed"}
            </button>
          ))}
        </div>

        <div style={{padding: "10px 14px", borderBottom: "1px solid #FFFFFF"}}>
          <div style={{color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", letterSpacing: "1px", marginBottom: 8}}>УЗЛЫ</div>
          {Object.entries(NODE_TYPES).map(([k, v]) => (
            <div
              key={k}
              onClick={() => setActiveNodeTypes(p => ({...p, [k]: !p[k]}))}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 5,
                cursor: "pointer",
                opacity: activeNodeTypes[k] ? 1 : 0.35
              }}>
              <div style={{width: 10, height: 10, borderRadius: 2, background: v.color, flexShrink: 0}}/>
              <span style={{color: "#FFFFFF", fontSize: "14px"}}>{v.label}</span>
            </div>
          ))}
        </div>

        <div style={{padding: "10px 14px"}}>
          <div style={{color: "#FFFFFF", fontSize: "20px", fontWeight: "bold", letterSpacing: "1px", marginBottom: 8}}>СВЯЗИ</div>
          {Object.entries(EDGE_TYPES).map(([k, v]) => (
            <div
              key={k}
              onClick={() => setActiveEdgeTypes(p => ({...p, [k]: !p[k]}))}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 5,
                cursor: "pointer",
                opacity: activeEdgeTypes[k] ? 1 : 0.35
              }}>
              <svg width="20" height="8">
                <line
                  x1="0"
                  y1="4"
                  x2="20"
                  y2="4"
                  stroke={v.color.slice(0, 7)}
                  strokeWidth={v.width}
                  strokeDasharray={v.dash}
                />
              </svg>
              <span style={{color: "#FFFFFF", fontSize: "14px"}}>{v.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{flex: 1, display: "flex", flexDirection: "column", position: "relative"}}>
        <div style={{
          height: "36px", background: "#132133", borderBottom: "1px solid #41618a",
          display: "flex", alignItems: "center", padding: "0 16px", gap: 24,
        }}>
          <span style={{ color: "#FFFFFF", fontSize: "11px" }}>
            Узлов: <span style={{ color: "#4A9EFF" }}>{stats.nodes}</span>
          </span>
          <span style={{ color: "#FFFFFF", fontSize: "11px" }}>
            Рёбер: <span style={{ color: "#4A9EFF" }}>{stats.edges}</span>
          </span>
          <span style={{ color: "#FFFFFF", fontSize: "11px" }}>
            {params.floors} эт. × {params.sections} секц. × {params.aptsPerFloor} кв.
          </span>
          <span style={{ color: "#FFFFFF", fontSize: "10px", marginLeft: "auto" }}>
            Scroll: zoom · Drag: pan · Node drag: перемещение
          </span>
        </div>

        <svg ref={svgRef} style={{flex: 1, background: "#0F1A2B"}}/>

        {hovered && (
          <div style={{
            position: "absolute",
            bottom: 16,
            right: 16,
            background: "#1C2E4A",
            border: "1px solid #52677D",
            padding: "10px 14px",
            borderRadius: 6,
            minWidth: 160,
          }}>
            <div style={{color: hovered.type.color, fontSize: "11px", marginBottom: 4}}>
              {hovered.type.label}
            </div>
            <div style={{ color: "#FFFFFF", fontSize: "14px" }}>{hovered.label}</div>
            {hovered.floor !== undefined && <div style={{ color: "#FFFFFF", fontSize: "14px", marginTop: 2 }}>Этаж: {hovered.floor}</div>}
            {hovered.section !== -1 && <div style={{ color: "#FFFFFF", fontSize: "14px" }}>Секция: {hovered.section + 1}</div>}
            <div style={{ color: "#FFFFFF", fontSize: "14px", marginTop: 2 }}>id: {hovered.id}</div>
          </div>
        )}
      </div>
    </div>
  );
}
