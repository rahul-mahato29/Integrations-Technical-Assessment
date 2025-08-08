import { Box, Button } from "@mui/material";
import axios from "axios";

// Maps integration types to their respective API endpoints
const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  Hubspot: "hubspot",
};

// Handles loading and clearing integration items
export const DataForm = ({ integrationType, credentials, setIntegrationParams }) => {
  const endpoint = endpointMapping[integrationType];

  // Fetch data from backend and update integrationParams
  const handleLoad = async () => {
    try {
      const formData = new FormData();
      formData.append("credentials", JSON.stringify(credentials));

      const { data } = await axios.post(
        `http://localhost:8000/integrations/${endpoint}/load`,
        formData
      );

      setIntegrationParams((prev) => ({
        ...prev,
        items: data,
      }));
    } catch (e) {
      alert(e?.response?.data?.detail);
    }
  };

  // Clear loaded items
  const handleClear = () => {
    setIntegrationParams((prev) => ({
      ...prev,
      items: [],
    }));
  };

  return (
    <Box
      display="flex"
      justifyContent="flex-start"
      alignItems="center"
      flexDirection="column"
      width="100%"
    >
      <Box display="flex" flexDirection="column" width="100%">
        <Button onClick={handleLoad} sx={{ mt: 2 }} variant="contained">
          Load Data
        </Button>
        <Button onClick={handleClear} sx={{ mt: 1 }} variant="contained">
          Clear Data
        </Button>
      </Box>
    </Box>
  );
};
