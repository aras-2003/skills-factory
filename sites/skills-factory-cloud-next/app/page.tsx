"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { callTool, SKILLS, SOURCE, TOOLS, type ToolOutput } from "@/lib/cloud-tools";

const samples: Record<string, unknown> = {
  runtime_info: {},
  list_skills: {},
  load_skill: { skill_name: "skill-test-design" },
  route_investment_request: { user_request: "Co zmieniło się w moim portfelu i co warto obserwować?" },
  render_bar_chart: { labels: ["Przykład A", "Przykład B", "Przykład C"], values: [30, 50, -10], title: "Jawne dane przykładowe", unit: "PLN", horizontal: true },
  render_line_chart: { x_labels: ["Q1", "Q2", "Q3", "Q4"], series_names: ["Seria A", "Seria B"], series_values: [[10, 24, 20, 35], [20, 15, 27, 32]], title: "Jawne dane przykładowe", unit: "PLN" },
};
type Result = ToolOutput;
function Console({ name }: { name: string }) {
  const [input, setInput] = useState(JSON.stringify(samples[name], null, 2));
  const [output, setOutput] = useState<Result | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const context = (document as unknown as { modelContext?: { registerTool: (tool: object, options: { signal: AbortSignal }) => void | Promise<void> } }).modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const tool = TOOLS.find(t => t.name === name)!;
    const execute = async (args: unknown) => {
      const result = await callTool(name, args);
      setInput(JSON.stringify(args, null, 2)); setOutput(result); setError("");
      return result;
    };
    try { void Promise.resolve(context.registerTool({ ...tool, annotations: { readOnlyHint: false, untrustedContentHint: true }, execute }, { signal: lifecycle.signal })).catch(() => undefined); } catch { /* Browser support is optional. */ }
    return () => lifecycle.abort();
  }, [name]);
  async function run() { try { setOutput(await callTool(name, JSON.parse(input))); setError(""); } catch (e) { setOutput(null); setError(e instanceof Error ? e.message : "Nieprawidłowe dane"); } }
  return <div className="console-grid"><section className="input-panel"><label htmlFor={name}>Argumenty JSON</label><Textarea id={name} value={input} onChange={e => setInput(e.target.value)} spellCheck={false} className="json-input"/><p className="hint">Przykłady są syntetyczne. Nic nie jest zapisywane.</p><Button onClick={run}>Uruchom obliczenie</Button></section><section className="output-panel" aria-live="polite"><div className="result-label">Wynik</div>{error ? <pre className="error" role="alert">{error}</pre> : output ? <>{"svg" in output && <div className="chart-scroll" dangerouslySetInnerHTML={{ __html: output.svg }}/>}<pre>{JSON.stringify("svg" in output ? { ...output, svg: "[SVG pokazany powyżej]" } : output, null, 2)}</pre></> : <div className="empty"><span className="empty-symbol">{ "{ }" }</span><p>Uruchom narzędzie, aby zobaczyć wynik.</p><p className="hint">Panel używa tego samego kodu obliczeń co MCP. Nie jest testem połączenia pluginu.</p></div>}</section></div>;
}
export default function Home() {
  return <main><header><Link className="brand" href="/" aria-label="Skills Factory Cloud"><span className="mark">S</span><span>Skills Factory <strong>Cloud</strong></span></Link><span className="draft">Site MCP · Lab {SOURCE.lab_release.version}</span></header><div className="workspace"><div className="intro"><div><p className="eyebrow">SKILLS FACTORY / RUNTIME</p><h1>Pełny katalog Skills Factory Lab</h1><p className="intro-copy">Prywatny Site MCP udostępnia wszystkie skille i workflowy Labu, niezależnie od statusu dojrzałości.</p></div><a className="repo-link" href={SOURCE.repository} target="_blank" rel="noreferrer">aras-2003 / skills-factory</a></div><Tabs defaultValue="runtime_info"><TabsList className="tool-tabs">{TOOLS.map(tool => <TabsTrigger key={tool.name} value={tool.name}>{tool.name}</TabsTrigger>)}</TabsList>{TOOLS.map(tool => <TabsContent key={tool.name} value={tool.name}><div className="tool-heading"><code>{tool.name}</code><span>read / compute only</span></div><Console name={tool.name}/></TabsContent>)}</Tabs><section className="contract"><div><h2>Granice wykonania</h2><p>Site udostępnia katalog, metadane i dokładne instrukcje SKILL.md. Host modelu wykonuje załadowane instrukcje; MCP nie udaje niezależnego agenta. Router i wykresy zachowują dotychczasowe ograniczenia.</p></div><div><h2>Połączenie MCP</h2><code>POST /mcp</code><p>Jedna nazwa runtime: <strong>skills-factory-runtime</strong>. Katalog odpowiada pełnemu artefaktowi Labu z main.</p></div></section><section className="contract"><div><h2>Skills Factory Lab</h2><p>{SKILLS.length} pozycji: 64 skille i 19 workflowów z Labu.</p></div><div className="skill-list">{SKILLS.map(skill => <code key={skill}>{skill}</code>)}</div></section><footer>Skills Factory Lab {SOURCE.lab_release.version} · źródło {SOURCE.github_main_revision.slice(0, 12)} · {SOURCE.channel}</footer></div></main>;
}
