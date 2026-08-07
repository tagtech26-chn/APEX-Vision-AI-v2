import {
    Box,
    Chip,
    Typography,
} from "@mui/material";

interface FilterChipsProps {

    title: string;

    items: string[];

    selected: string;

    onSelect: (value: string) => void;

}

export default function FilterChips({

    title,

    items,

    selected,

    onSelect,

}: FilterChipsProps) {

    return (

        <Box sx={{ mb: 2 }}>

            <Typography

                variant="subtitle2"

                sx={{ fontWeight: 700, mb: 1 }}

            >

                {title}

            </Typography>

            <Box

                sx={{

                    display: "flex",

                    gap: 1,

                    flexWrap: "wrap",

                }}

            >

                <Chip

                    label="All"

                    clickable

                    color={selected === "" ? "primary" : "default"}

                    onClick={() => onSelect("")}

                />

                {

                    items.map(item => (

                        <Chip

                            key={item}

                            label={item}

                            clickable

                            color={selected === item ? "primary" : "default"}

                            onClick={() => onSelect(item)}

                        />

                    ))

                }

            </Box>

        </Box>

    );

}