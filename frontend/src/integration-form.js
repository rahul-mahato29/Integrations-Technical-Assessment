import { useState } from "react";
import {
  Box,
  Autocomplete,
  TextField,
  Typography,
  Divider,
  Paper,
  Card,
  CardContent,
} from "@mui/material";

import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubspotIntegration } from "./integrations/hubspot";
import { DataForm } from "./data-form";

// Maps integration types to their respective component
const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  Hubspot: HubspotIntegration,
};

// Format object keys for display (created_time → Created Time)
const formatKey = (key) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState("TestUser");
  const [org, setOrg] = useState("TestOrg");
  const [currType, setCurrType] = useState(null);
  const CurrIntegration = integrationMapping[currType];

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#fdf9f2", p: 4 }}>
      <Paper
        elevation={3}
        sx={{
          display: "flex",
          borderRadius: 2,
          overflow: "hidden",
          height: "calc(100vh - 64px)",
        }}
      >
        {/* Left: Form Section */}
        <Box
          sx={{
            flex: 1,
            p: 4,
            bgcolor: "#fff",
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-start",
            height: "100%",
            overflow: "hidden",
          }}
        >
          <Typography variant="h6" gutterBottom>
            User Details
          </Typography>

          <TextField
            label="User"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            sx={{ mt: 2 }}
            fullWidth
          />

          <TextField
            label="Organization"
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            sx={{ mt: 2 }}
            fullWidth
          />

          <Autocomplete
            id="integration-type"
            options={Object.keys(integrationMapping)}
            renderInput={(params) => (
              <TextField {...params} label="Integration Type" />
            )}
            sx={{ mt: 2 }}
            onChange={(e, value) => setCurrType(value)}
          />

          {/* Show integration-specific auth UI */}
          {currType && (
            <Box>
              <CurrIntegration
                user={user}
                org={org}
                integrationParams={integrationParams}
                setIntegrationParams={setIntegrationParams}
              />
            </Box>
          )}

          {/* Show Load/Clear buttons after credentials are available */}
          {integrationParams?.credentials && (
            <Box sx={{ mt: 2 }}>
              <DataForm
                integrationType={integrationParams?.type}
                credentials={integrationParams?.credentials}
                setIntegrationParams={setIntegrationParams}
              />
            </Box>
          )}
        </Box>

        {/* Divider between form and data display */}
        <Divider orientation="vertical" flexItem sx={{ bgcolor: "#ccc" }} />

        {/* Right: Dynamic Data Display */}
        <Box sx={{ flex: 1.5, p: 4, bgcolor: "#eaf4ff", height: "100%", overflowY: "auto" }}>
          <Typography variant="h6" gutterBottom> Loaded Integration Items </Typography>

          {integrationParams?.items?.length > 0 ? (
            integrationParams.items.map((item, index) => (
            <Card key={index} sx={{ mb: 2, backgroundColor: "#fff", borderRadius: 2 }}>
                <CardContent>
                  {/* Card Title: Show name prominently if available */}
                  {item.name && (
                    <Typography variant="subtitle1" sx={{ fontWeight: 700, color: "#000", mb: 1 }}>
                      {item.name}
                    </Typography>
                  )}

                  {/* Display all other key-values except falsy or "N/A"/null */}
                  {Object.entries(item).map(([key, value], idx) => {
                    const stringVal = String(value ?? "N/A");
                    if (
                      key === "name" ||
                      !stringVal ||
                      stringVal.toLowerCase() === "n/a" ||
                      stringVal.toLowerCase() === "null" ||
                      stringVal === "undefined"
                    ) {
                      return null;
                    }

                    return (
                      <Typography key={`${index}-${key}`} variant="body2" color="text.secondary">
                        {formatKey(key)}: {stringVal}
                      </Typography>
                    );
                  })}
                </CardContent>
             </Card>
            ))
          ) : (
            <Typography variant="body2" color="text.secondary"> No data loaded yet.</Typography>
          )}
        </Box>
      </Paper>
    </Box>
  );
};
