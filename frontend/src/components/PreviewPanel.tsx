import {
  Box,
  Paper,
  Typography,
} from "@mui/material";

export default function PreviewPanel() {

  return (

    <Paper
      elevation={3}
      sx={{
        height: 600,
        overflow: "hidden",
        borderRadius: 3,
      }}
    >

      <Box

        sx={{

          width: "100%",

          height: "100%",

          display: "flex",

          alignItems: "center",

          justifyContent: "center",

          bgcolor: "#eeeeee",

        }}

      >

        <Typography variant="h4">

          LIVE PREVIEW

        </Typography>

      </Box>

    </Paper>

  );

}