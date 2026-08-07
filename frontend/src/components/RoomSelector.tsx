import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";

export default function RoomSelector() {
  return (
    <Stack
      direction="row"
      spacing={3}
      sx={{
        mb: 2,
        alignItems: "center",
      }}
    >
      <Typography
        variant="h6"
      >
        Room
      </Typography>

      <FormControl
        sx={{
          width: 300,
        }}
      >
        <InputLabel>
          Select Room
        </InputLabel>

        <Select
          defaultValue={1}
          label="Select Room"
        >
          <MenuItem value={1}>
            Living Room
          </MenuItem>

          <MenuItem value={2}>
            Bedroom
          </MenuItem>

          <MenuItem value={3}>
            Kitchen
          </MenuItem>
        </Select>

      </FormControl>
    </Stack>
  );
}