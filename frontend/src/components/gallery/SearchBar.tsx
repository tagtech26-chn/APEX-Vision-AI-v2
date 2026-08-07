import {
    TextField,
    InputAdornment,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";

interface SearchBarProps {

    value: string;

    onChange: (value: string) => void;

}

export default function SearchBar({

    value,

    onChange,

}: SearchBarProps) {

    return (

        <TextField

            fullWidth

            size="small"

            placeholder="Search tiles by name, manufacturer or series..."

            value={value}

            onChange={(e) => onChange(e.target.value)}

            slotProps={{

                input: {

                    startAdornment: (

                        <InputAdornment position="start">

                            <SearchIcon color="action" />

                        </InputAdornment>

                    ),

                },

            }}

        />

    );

}