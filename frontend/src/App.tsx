import { useEffect, useState, type ReactNode } from "react";
import { Box, Button, Chip, Divider, FormControl, IconButton, MenuItem, Select, Switch, Tooltip, Typography } from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import ViewInArOutlinedIcon from "@mui/icons-material/ViewInArOutlined";
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import GridViewOutlinedIcon from "@mui/icons-material/GridViewOutlined";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import CompareOutlinedIcon from "@mui/icons-material/CompareOutlined";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import StraightenOutlinedIcon from "@mui/icons-material/StraightenOutlined";
import PublicOutlinedIcon from "@mui/icons-material/PublicOutlined";
import { API } from "./config";
import { getDiagnostics, submitAndWaitRender } from "./services/api";
import { useRenderStore } from "./store/renderStore";
import BottomGallery from "./components/gallery/BottomGallery";
import RoomSelectionDialog from "./components/rooms/RoomSelectionDialog";

const nav = [["Dashboard", DashboardOutlinedIcon], ["Visualizer", ViewInArOutlinedIcon], ["Upload Image", CloudUploadOutlinedIcon], ["Catalog", GridViewOutlinedIcon], ["Projects", FolderOpenOutlinedIcon], ["AI Analysis", AutoAwesomeIcon], ["Compare", CompareOutlinedIcon], ["History", HistoryOutlinedIcon], ["Reports", AssessmentOutlinedIcon], ["Settings", SettingsOutlinedIcon]] as const;

function SectionLabel({ children }: { children: ReactNode }) {
  return <Typography sx={{ color: "#f1f4f8", fontSize: 12, fontWeight: 800, mb: 1.25 }}>{children}</Typography>;
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", py: .7 }}><Typography sx={{ color: "#aeb8c5", fontSize: 12 }}>{label}</Typography><Switch size="small" checked={checked} onChange={(e) => onChange(e.target.checked)} sx={{ "& .MuiSwitch-switchBase.Mui-checked": { color: "#8b5cf6" }, "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": { bgcolor: "#6840e8" } }} /></Box>;
}

export default function App() {
  const image = useRenderStore((s) => s.image);
  const room = useRenderStore((s) => s.room);
  const roomName = useRenderStore((s) => s.roomName);
  const tile = useRenderStore((s) => s.tile);
  const groutWidth = useRenderStore((s) => s.groutWidth);
  const loading = useRenderStore((s) => s.loading);
  const progress = useRenderStore((s) => s.progress);
  const progressMessage = useRenderStore((s) => s.progressMessage);
  const tileSize = useRenderStore((s) => s.tileSize);
  const setTileSize = useRenderStore((s) => s.setTileSize);
  const pattern = useRenderStore((s) => s.pattern);
  const setPattern = useRenderStore((s) => s.setPattern);
  const setImage = useRenderStore((s) => s.setImage);
  const setLoading = useRenderStore((s) => s.setLoading);
  const setProgress = useRenderStore((s) => s.setProgress);
  const setProgressMessage = useRenderStore((s) => s.setProgressMessage);
  const setRoomDialogOpen = useRenderStore((s) => s.setRoomDialogOpen);

  const [surface, setSurface] = useState("Floor");
  const [view, setView] = useState<"realistic" | "material">("realistic");
  const [environment, setEnvironment] = useState<"interior" | "exterior">("interior");
  const [smartRemoval, setSmartRemoval] = useState(true);
  const [furnitureShadow, setFurnitureShadow] = useState(true);
  const [enhanceLighting, setEnhanceLighting] = useState(false);
  const [providerLabel, setProviderLabel] = useState("V2.2 AI");
  const [geometryLabel, setGeometryLabel] = useState("Gemini advisor · disabled");
  const imageUrl = image.startsWith("http") ? image : `${API}${image}`;

  useEffect(() => {
    let active = true;
    getDiagnostics().then((diagnostics) => {
      if (!active) return;
      const names = Object.values(diagnostics.ai.providers).join(" + ");
      const configured = diagnostics.ai.configured_provider === "light" ? "Light AI" : diagnostics.ai.configured_provider === "v22" ? "V2.2 AI" : "Heavy AI";
      setProviderLabel(diagnostics.ai.analyzer_loaded && names ? `${configured} · ${names}` : `${configured} · warming`);
      const advisor = diagnostics.ai.geometry_advisor;
      if (advisor?.provider === "gemini") {
        setGeometryLabel(advisor.enabled ? `Gemini · ${advisor.status || "configured"}` : "Gemini · API key missing");
      } else {
        setGeometryLabel("Gemini advisor · disabled");
      }
    }).catch(() => {
      if (!active) return;
      setProviderLabel("V2.2 AI · unavailable");
      setGeometryLabel("Gemini advisor · unavailable");
    });
    return () => { active = false; };
  }, []);

  const handleRender = async () => {
    setLoading(true);
    setProgress(0);
    setProgressMessage("Queued for V2.2 AI geometry rendering...");
    try {
      const job = await submitAndWaitRender({
        room,
        tile,
        tile_size: tileSize,
        grout_width: groutWidth,
        grout_color: [220, 220, 220],
        pattern,
        material_profile: "auto",
      }, (current) => {
        setProgress(current.progress);
        setProgressMessage(current.message || "V2.2 AI geometry rendering...");
      });
      if (job.status !== "done" || !job.image) throw new Error(job.message || "Render failed");
      setImage(`${job.image}?t=${Date.now()}`);
      setProgress(1);
      setProgressMessage(`Done · ${job.duration_seconds ?? 0}s`);
    } catch (error) {
      setProgressMessage(error instanceof Error ? error.message : "Render failed");
    } finally {
      setLoading(false);
    }
  };

  return <Box sx={{ minHeight: "100vh", bgcolor: "#070c12", color: "#fff", display: "flex", overflow: "hidden", fontFamily: "Inter, Segoe UI, sans-serif" }}>
    <Box component="aside" sx={{ width: 212, flexShrink: 0, bgcolor: "#090f16", borderRight: "1px solid #1d2732", display: "flex", flexDirection: "column", zIndex: 1300 }}>
      <Box sx={{ height: 58, display: "flex", alignItems: "center", gap: 1.25, px: 2, borderBottom: "1px solid #1d2732" }}><Box sx={{ width: 25, height: 25, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "#7045ed", boxShadow: "0 0 18px rgba(112,69,237,.45)" }}><AutoAwesomeIcon sx={{ fontSize: 15 }} /></Box><Typography sx={{ fontWeight: 800, letterSpacing: .2, fontSize: 16 }}>APEX Vision AI</Typography><Chip label="v2.2" size="small" sx={{ height: 20, ml: "auto", bgcolor: "#202832", color: "#9aa5b2", fontSize: 9 }} /></Box>
      <Box sx={{ px: 1.5, py: 2, flex: 1 }}>
        {nav.map(([label, Icon], index) => <Button key={label} fullWidth startIcon={<Icon sx={{ fontSize: 18 }} />} sx={{ justifyContent: "flex-start", color: index === 1 ? "#fff" : "#c3cbd5", bgcolor: index === 1 ? "#2a1b5b" : "transparent", borderRadius: 1.25, mb: .45, py: .9, px: 1.25, textTransform: "none", fontSize: 12, fontWeight: index === 1 ? 700 : 500, "&:hover": { bgcolor: "#171f2a" }, "& .MuiButton-startIcon": { color: index === 1 ? "#b18cff" : "#d0d7df" } }}>{label}</Button>)}
        <Box sx={{ mt: 2, border: "1px solid #1d2732", borderRadius: 1.5, p: 1.5, bgcolor: "#0c131b" }}><Typography sx={{ color: "#f0f3f7", fontSize: 10, fontWeight: 800, mb: 1.4 }}>SYSTEM STATUS</Typography>{["AI Provider", "Geometry Advisor", "Floor Detection", "Render Engine"].map((label, i) => <Box key={label} sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}><Typography sx={{ color: "#8995a3", fontSize: 9 }}>{label}</Typography><Chip label={i === 0 ? providerLabel : i === 1 ? geometryLabel : "Enabled"} size="small" sx={{ height: 18, bgcolor: "#15351f", color: "#61d884", fontSize: 8, maxWidth: 150 }} /></Box>)}<Box sx={{ display: "flex", alignItems: "center", gap: .7, mt: 1 }}><Box sx={{ width: 7, height: 7, borderRadius: "50%", bgcolor: "#39c96a" }} /><Typography sx={{ color: "#52d47a", fontSize: 9 }}>Operational</Typography></Box><Typography sx={{ color: "#697685", fontSize: 9, mt: 1 }}>Version v2.2 · Geometry Lab</Typography></Box>
      </Box>
      <Button startIcon={<AutoAwesomeIcon />} sx={{ mx: 1, mb: 1.5, justifyContent: "flex-start", color: "#e2dcff", bgcolor: "#261b52", textTransform: "none", fontSize: 11, borderRadius: 1.25 }}>Documentation</Button>
    </Box>

    <Box component="main" sx={{ minWidth: 0, flex: 1, position: "relative", height: "100vh", bgcolor: "#080e15" }}>
      <Box sx={{ height: 58, display: "flex", alignItems: "center", px: 2, borderBottom: "1px solid #1d2732", bgcolor: "#0a1119" }}><Typography sx={{ fontSize: 18, fontWeight: 800 }}>Project: {roomName}</Typography><IconButton size="small" sx={{ color: "#c4cbd5", ml: .5 }}><EditOutlinedIcon sx={{ fontSize: 16 }} /></IconButton><Box sx={{ flex: 1 }} /><Button onClick={() => setRoomDialogOpen(true)} variant="outlined" startIcon={<FolderOpenOutlinedIcon />} sx={{ borderColor: "#7345ed", color: "#fff", textTransform: "none", fontSize: 11, mr: 1, borderRadius: 1 }}>New Project</Button><Button onClick={() => window.open(imageUrl, "_blank")} variant="contained" startIcon={<DownloadOutlinedIcon />} sx={{ bgcolor: "#7141e8", textTransform: "none", fontSize: 11, borderRadius: 1, "&:hover": { bgcolor: "#8156f3" } }}>Export</Button><Tooltip title="Help"><IconButton sx={{ ml: 1, color: "#d1d7df" }}><HelpOutlineOutlinedIcon /></IconButton></Tooltip><Tooltip title="Settings"><IconButton sx={{ color: "#d1d7df" }}><SettingsOutlinedIcon /></IconButton></Tooltip><Box sx={{ ml: 1, width: 28, height: 28, borderRadius: "50%", bgcolor: "#6952e9", display: "grid", placeItems: "center", fontSize: 10, fontWeight: 800 }}>AD</Box></Box>

      <Box sx={{ position: "absolute", top: 58, left: 0, right: 294, bottom: 274, p: 1.75 }}><Box sx={{ position: "relative", width: "100%", height: "100%", minHeight: 300, bgcolor: "#05080c", borderRadius: 1, border: "1px solid #1e2a36", overflow: "hidden" }}><Box sx={{ position: "absolute", top: 0, left: 0, right: 0, height: 44, display: "flex", alignItems: "center", px: 1.5, bgcolor: "rgba(5,9,14,.72)", zIndex: 5 }}><Typography sx={{ fontSize: 11, fontWeight: 700, color: "#dce2e9" }}>Rendered Scene</Typography><Box sx={{ flex: 1 }} /><Typography sx={{ fontSize: 11, color: "#aeb7c3" }}>Detection: <b style={{ color: "#e5e9ef" }}>{surface}</b></Typography><Typography sx={{ ml: 1.5, fontSize: 11, color: "#4bd274", fontWeight: 700 }}>✓ V2.2 AI · {geometryLabel}</Typography></Box><Box component="img" src={imageUrl} alt="APEX visualizer" sx={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }} />{loading && <Box sx={{ position: "absolute", inset: 0, bgcolor: "rgba(4,7,11,.58)", backdropFilter: "blur(3px)", display: "grid", placeItems: "center", zIndex: 10 }}><Box sx={{ width: 300 }}><Typography sx={{ textAlign: "center", mb: 1, fontSize: 12 }}>{progressMessage || "V2.2 AI geometry rendering..."}</Typography><Box sx={{ height: 4, bgcolor: "#26303b", borderRadius: 2, overflow: "hidden" }}><Box sx={{ width: `${Math.round(progress * 100)}%`, height: "100%", bgcolor: "#7447ff", transition: "width .2s" }} /></Box></Box></Box>}<Box sx={{ position: "absolute", left: 12, bottom: 12, display: "flex", gap: 1, zIndex: 6 }}><Button size="small" startIcon={<CompareOutlinedIcon />} sx={{ bgcolor: "rgba(250,250,250,.94)", color: "#20242a", textTransform: "none", fontSize: 10, minWidth: 0, px: 1.2 }}>Before / After</Button><Button size="small" startIcon={<ImageOutlinedIcon />} sx={{ bgcolor: "rgba(250,250,250,.94)", color: "#20242a", textTransform: "none", fontSize: 10, minWidth: 0, px: 1.2 }}>Original</Button></Box></Box></Box>

      <Box component="aside" sx={{ position: "absolute", top: 68, right: 8, width: 278, bottom: 274, bgcolor: "#0b121a", border: "1px solid #202c38", borderRadius: 1.5, overflowY: "auto", zIndex: 1100, boxShadow: "0 16px 40px rgba(0,0,0,.28)" }}><Box sx={{ display: "flex", height: 48, borderBottom: "1px solid #202c38" }}><Button sx={{ flex: 1, color: "#fff", borderBottom: "2px solid #7a49f4", borderRadius: 0, textTransform: "none", fontSize: 11, fontWeight: 800 }}>Scene</Button><Button sx={{ flex: 1, color: "#8793a0", borderRadius: 0, textTransform: "none", fontSize: 11 }}>AI Analysis</Button></Box><Box sx={{ p: 2 }}>
        <SectionLabel>Surface Detection</SectionLabel><Typography sx={{ color: "#8b96a4", fontSize: 10, mb: .65 }}>Detected Surface</Typography><FormControl fullWidth size="small"><Select value={surface} onChange={(e) => setSurface(e.target.value)} sx={{ color: "#e7ebf0", bgcolor: "#111923", fontSize: 11, ".MuiOutlinedInput-notchedOutline": { borderColor: "#2a3745" } }}><MenuItem value="Floor">Floor</MenuItem><MenuItem value="Wall">Wall</MenuItem><MenuItem value="Ceiling">Ceiling</MenuItem></Select></FormControl><Typography sx={{ color: "#8b96a4", fontSize: 10, mt: 2 }}>Surface Area</Typography><Typography sx={{ color: "#f0f3f7", fontSize: 13, fontWeight: 700, mt: .4 }}>V2.2 geometry pipeline</Typography><Divider sx={{ my: 2, borderColor: "#202c38" }} />
        <SectionLabel>Gemini Geometry Advisor</SectionLabel><Box sx={{ border: "1px solid #263240", borderRadius: 1, p: 1.2, bgcolor: "#101822" }}><Typography sx={{ color: "#f0f3f7", fontSize: 11, fontWeight: 800 }}>Gemini Vision</Typography><Typography sx={{ color: "#8b96a4", fontSize: 9, mt: .5 }}>{geometryLabel}</Typography><Typography sx={{ color: "#697685", fontSize: 9, mt: .7 }}>Advisory only · CV floor mask remains authoritative</Typography></Box><Divider sx={{ my: 2, borderColor: "#202c38" }} />
        <SectionLabel>Visualization Mode</SectionLabel><Box sx={{ display: "flex", border: "1px solid #263240", borderRadius: 1, overflow: "hidden" }}><Button onClick={() => setView("realistic")} sx={{ flex: 1, bgcolor: view === "realistic" ? "#6040cf" : "transparent", color: "#fff", borderRadius: 0, textTransform: "none", fontSize: 10 }}>Realistic</Button><Button onClick={() => setView("material")} sx={{ flex: 1, bgcolor: view === "material" ? "#6040cf" : "transparent", color: "#fff", borderRadius: 0, textTransform: "none", fontSize: 10 }}>Material Only</Button></Box>
        <SectionLabel>Environment</SectionLabel><Box sx={{ display: "flex", border: "1px solid #263240", borderRadius: 1, overflow: "hidden" }}><Button onClick={() => setEnvironment("interior")} sx={{ flex: 1, bgcolor: environment === "interior" ? "#6040cf" : "transparent", color: "#fff", borderRadius: 0, textTransform: "none", fontSize: 10 }}>Interior</Button><Button onClick={() => setEnvironment("exterior")} sx={{ flex: 1, bgcolor: environment === "exterior" ? "#6040cf" : "transparent", color: "#fff", borderRadius: 0, textTransform: "none", fontSize: 10 }}>Exterior</Button></Box>
        <SectionLabel>Options</SectionLabel><ToggleRow label="Smart Removal" checked={smartRemoval} onChange={setSmartRemoval} /><ToggleRow label="Furniture Shadow" checked={furnitureShadow} onChange={setFurnitureShadow} /><ToggleRow label="Enhance Lighting" checked={enhanceLighting} onChange={setEnhanceLighting} /><Divider sx={{ my: 1.5, borderColor: "#202c38" }} />
        <SectionLabel>Material Settings</SectionLabel><Typography sx={{ color: "#8b96a4", fontSize: 10, mb: .6 }}>Tile Size</Typography><FormControl fullWidth size="small"><Select value={tileSize} onChange={(e) => setTileSize(Number(e.target.value))} sx={{ color: "#e7ebf0", bgcolor: "#111923", fontSize: 11, ".MuiOutlinedInput-notchedOutline": { borderColor: "#2a3745" } }}>{[300,400,450,600,800,1000,1200].map((size) => <MenuItem key={size} value={size}>{size} × {size}</MenuItem>)}</Select></FormControl><Typography sx={{ color: "#8b96a4", fontSize: 10, mt: 1.5, mb: .6 }}>Pattern</Typography><FormControl fullWidth size="small"><Select value={pattern} onChange={(e) => setPattern(e.target.value)} sx={{ color: "#e7ebf0", bgcolor: "#111923", fontSize: 11, ".MuiOutlinedInput-notchedOutline": { borderColor: "#2a3745" } }}>{["Straight","Brick","Herringbone","Chevron"].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}</Select></FormControl><Box sx={{ display: "flex", gap: .7, mt: 1.5 }}><Chip icon={<StraightenOutlinedIcon />} label={`${groutWidth} mm grout`} size="small" sx={{ bgcolor: "#141e29", color: "#aab5c1", fontSize: 9 }} /><Chip icon={<PublicOutlinedIcon />} label={environment} size="small" sx={{ bgcolor: "#141e29", color: "#aab5c1", fontSize: 9 }} /></Box><Button fullWidth onClick={handleRender} disabled={loading} startIcon={<AutoAwesomeIcon />} sx={{ mt: 2, py: 1.15, bgcolor: "#7141e8", color: "#fff", textTransform: "none", fontSize: 11, fontWeight: 800, borderRadius: 1, "&:hover": { bgcolor: "#8055f4" }, "&.Mui-disabled": { bgcolor: "#2d2450", color: "#8f86ad" } }}>Apply &amp; Re-render</Button>
      </Box></Box>

      <BottomGallery />
      <RoomSelectionDialog />
    </Box>
  </Box>;
}
