import {
    Paper,
    Box,
    Typography,
    IconButton,
    Collapse,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Slider,
    ToggleButtonGroup,
    ToggleButton,
    Divider,
} from "@mui/material";

import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import SettingsIcon from "@mui/icons-material/Settings";

import { useRenderStore } from "../../store/renderStore";

const GROUT_COLOURS: { label: string; value: string; color: number[] }[] = [
    { label: "White", value: JSON.stringify([255, 255, 255]), color: [255, 255, 255] },
    { label: "Light Grey", value: JSON.stringify([220, 220, 220]), color: [220, 220, 220] },
    { label: "Grey", value: JSON.stringify([180, 180, 180]), color: [180, 180, 180] },
    { label: "Black", value: JSON.stringify([60, 60, 60]), color: [60, 60, 60] },
];

export default function FloatingPanel() {

    const panelOpen = useRenderStore((s) => s.panelOpen);
    const setPanelOpen = useRenderStore((s) => s.setPanelOpen);

    const tileSize = useRenderStore((s) => s.tileSize);
    const setTileSize = useRenderStore((s) => s.setTileSize);

    const groutWidth = useRenderStore((s) => s.groutWidth);
    const setGroutWidth = useRenderStore((s) => s.setGroutWidth);

    const groutColor = useRenderStore((s) => s.groutColor);
    const setGroutColor = useRenderStore((s) => s.setGroutColor);

    const pattern = useRenderStore((s) => s.pattern);
    const setPattern = useRenderStore((s) => s.setPattern);

    return (

        <Paper

            elevation={10}

            sx={{

                position: "absolute",

                top: 60,

                left: 20,

                width: panelOpen ? 340 : 56,

                overflow: "hidden",

                transition: "all .30s ease",

                borderRadius: 4,

                backdropFilter: "blur(20px)",

                background: "rgba(255,255,255,.82)",

                border: "1px solid rgba(255,255,255,.35)",

                boxShadow: "0 20px 45px rgba(0,0,0,.20)",

                zIndex: 100,

            }}

        >

            <Box

                sx={{

                    display: "flex",

                    alignItems: "center",

                    justifyContent: panelOpen ? "space-between" : "center",

                    p: 1,

                }}

            >

                {

                    panelOpen &&

                    <Typography

                        sx={{

                            fontWeight: 700,

                            fontSize: 18,

                        }}

                    >

                        Configure

                    </Typography>

                }

                <IconButton

                    onClick={() =>

                        setPanelOpen(!panelOpen)

                    }

                >

                    {

                        panelOpen

                            ?

                            <ChevronLeftIcon/>

                            :

                            <SettingsIcon/>

                    }

                </IconButton>

            </Box>

            <Collapse in={panelOpen}>

                <Divider/>

                <Box sx={{ p: 2 }}>

                    <FormControl

                        fullWidth

                        sx={{ mb: 2 }}

                    >

                        <InputLabel>

                            Tile Size

                        </InputLabel>

                        <Select

                            value={tileSize}

                            label="Tile Size"

                            onChange={(e) =>

                                setTileSize(Number(e.target.value))

                            }

                            MenuProps={{

                                slotProps: {

                                    paper: { sx: { zIndex: 1400 } },

                                    list: { sx: { zIndex: 1400 } },

                                },

                            }}

                        >

                            <MenuItem value={300}>

                                300 × 300

                            </MenuItem>

                            <MenuItem value={400}>

                                400 × 400

                            </MenuItem>

                            <MenuItem value={450}>

                                450 × 450

                            </MenuItem>

                            <MenuItem value={600}>

                                600 × 600

                            </MenuItem>

                            <MenuItem value={800}>

                                800 × 800

                            </MenuItem>

                            <MenuItem value={1000}>

                                1000 × 1000

                            </MenuItem>

                            <MenuItem value={1200}>

                                1200 × 1200

                            </MenuItem>

                        </Select>

                    </FormControl>

                    <Typography

                        sx={{

                            fontWeight: 600,

                        }}

                        gutterBottom

                    >

                        Grout Width

                    </Typography>

                    <Slider

                        value={groutWidth}

                        min={1}

                        max={10}

                        step={1}

                        valueLabelDisplay="auto"

                        onChange={(_event, value) =>

                            setGroutWidth(value as number)

                        }

                    />

                    <Typography

                        sx={{

                            fontWeight: 600,

                            mt: 3,

                        }}

                        gutterBottom

                    >

                        Grout Colour

                    </Typography>

                    <ToggleButtonGroup

                        exclusive

                        fullWidth

                        value={JSON.stringify(groutColor)}

                        onChange={(_event, value) => {

                            if (!value) return;

                            setGroutColor(JSON.parse(value));

                        }}

                    >

                        {GROUT_COLOURS.map((option) => (

                            <ToggleButton

                                key={option.value}

                                value={option.value}

                                title={option.label}

                            >

                                {option.color[0] > 180 ? "⬜" : option.color[0] > 120 ? "◻" : "◼"}

                            </ToggleButton>

                        ))}

                    </ToggleButtonGroup>

                    <Typography

                        sx={{

                            fontWeight: 600,

                            mt: 3,

                        }}

                        gutterBottom

                    >

                        Pattern

                    </Typography>

                    <Select

                        fullWidth

                        value={pattern}

                        onChange={(e) => setPattern(e.target.value)}

                        MenuProps={{

                            slotProps: {

                                paper: { sx: { zIndex: 1400 } },

                                list: { sx: { zIndex: 1400 } },

                            },

                        }}

                    >

                        <MenuItem value="Straight">

                            Straight

                        </MenuItem>

                        <MenuItem value="Brick">

                            Brick

                        </MenuItem>

                        <MenuItem value="Herringbone">

                            Herringbone

                        </MenuItem>

                        <MenuItem value="Chevron">

                            Chevron

                        </MenuItem>

                    </Select>

                </Box>

            </Collapse>

        </Paper>

    );

}
