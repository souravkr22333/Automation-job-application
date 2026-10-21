// frontend/src/components/profile/LanguagesTab.jsx
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Chip,
  Stack,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Language as LanguageIcon,
} from '@mui/icons-material';
import { useProfile } from '../../hooks/useProfile';

const LanguagesTab = () => {
  const {
    languages,
    languagesLoading,
    createLanguage,
    updateLanguage,
    deleteLanguage,
    isCreatingLanguage,
    isUpdatingLanguage,
    isDeletingLanguage,
  } = useProfile();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', proficiency: 'intermediate', is_native: false });

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData({ name: '', proficiency: 'intermediate', is_native: false });
    setOpenDialog(true);
  };

  const handleOpenEdit = (lang) => {
    setEditingId(lang.id);
    setFormData({ name: lang.name, proficiency: lang.proficiency, is_native: lang.is_native });
    setOpenDialog(true);
  };

  const handleClose = () => {
    setOpenDialog(false);
    setEditingId(null);
    setFormData({ name: '', proficiency: 'intermediate', is_native: false });
  };

  const handleSave = () => {
    if (editingId) {
      updateLanguage({ id: editingId, data: formData });
    } else {
      createLanguage(formData);
    }
    handleClose();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this language?')) {
      deleteLanguage(id);
    }
  };

  if (languagesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div className="bg-gray-800 p-3 pt-5 rounded-2xl">
      <div className="flex justify-between border-b w-auto mb-3">
        <div>
          <p>Languages</p>
        </div>
        <div className="text-blue-600">
          <button className="btn btn-info" onClick={handleOpenCreate}>
            <AddIcon />
            Add Language
          </button>
        </div>
      </div>



      {languages.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <LanguageIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="textSecondary" sx={{ mt: 2 }}>
            No Languages Added
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Add languages you speak
          </Typography>
        </Box>
      ) : (
        <List>
          {languages.map((lang) => (
            <ListItem key={lang.id} divider>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" fontWeight="bold">
                      {lang.name}
                    </Typography>
                    {lang.is_native && (
                      <Chip label="Native" size="small" color="primary" />
                    )}
                    <Chip 
                      label={lang.proficiency} 
                      size="small" 
                      variant="outlined"
                      color={
                        lang.proficiency === 'native' ? 'primary' :
                        lang.proficiency === 'advanced' || lang.proficiency === 'proficient' ? 'success' :
                        lang.proficiency === 'intermediate' || lang.proficiency === 'upper_intermediate' ? 'warning' :
                        'default'
                      }
                    />
                  </Box>
                }
                secondary={`Proficiency: ${lang.proficiency}`}
              />
              <ListItemSecondaryAction>
                <IconButton onClick={() => handleOpenEdit(lang)} size="small" color="primary">
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton 
                  onClick={() => handleDelete(lang.id)} 
                  size="small" 
                  color="error"
                  disabled={isDeletingLanguage}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingId ? 'Edit Language' : 'Add Language'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Language Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Proficiency Level</InputLabel>
                <Select
                  value={formData.proficiency || 'intermediate'}
                  onChange={(e) => setFormData({ ...formData, proficiency: e.target.value })}
                  label="Proficiency Level"
                >
                  <MenuItem value="beginner">Beginner</MenuItem>
                  <MenuItem value="elementary">Elementary</MenuItem>
                  <MenuItem value="intermediate">Intermediate</MenuItem>
                  <MenuItem value="upper_intermediate">Upper Intermediate</MenuItem>
                  <MenuItem value="advanced">Advanced</MenuItem>
                  <MenuItem value="proficient">Proficient</MenuItem>
                  <MenuItem value="native">Native</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_native || false}
                    onChange={(e) => setFormData({ ...formData, is_native: e.target.checked })}
                  />
                }
                label="Native Language"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={isCreatingLanguage || isUpdatingLanguage}
          >
            {isCreatingLanguage || isUpdatingLanguage ? (
              <CircularProgress size={24} />
            ) : editingId ? (
              'Update'
            ) : (
              'Add'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default LanguagesTab;