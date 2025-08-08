import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot'
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                {loadedData && (
                  <Box
                    sx={{
                      mt: 2,
                      width: '100%',
                      bgcolor: '#f5f5f5',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      maxHeight: 300,
                      overflowY: 'auto'
                    }}
                  >
                    {JSON.stringify(loadedData, null, 2)}
                  </Box>
                )}
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
