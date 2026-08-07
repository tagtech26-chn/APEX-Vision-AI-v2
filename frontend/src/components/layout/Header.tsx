import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";

import SettingsIcon from "@mui/icons-material/Settings";
import FullscreenIcon from "@mui/icons-material/Fullscreen";

export default function Header() {
  return (
    <AppBar
      position="absolute"
      elevation={0}
      sx={{
        background: "rgba(0,0,0,0.55)",
        backdropFilter: "blur(12px)",
      }}
    >
      <Toolbar>

        <Typography
          variant="h5"
          sx={{ fontWeight: "bold" }}
        >
          APEX Vision AI
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        <IconButton color="inherit">
          <FullscreenIcon />
        </IconButton>

        <IconButton color="inherit">
          <SettingsIcon />
        </IconButton>

      </Toolbar>
    </AppBar>
  );
}