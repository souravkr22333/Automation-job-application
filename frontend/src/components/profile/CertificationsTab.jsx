// frontend/src/components/profile/CertificationsTab.jsx
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
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
  Switch,
  FormControlLabel,
  Chip,
  Stack,
  CircularProgress,
  Autocomplete,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Book as CertificationIcon,
} from '@mui/icons-material';
import { useProfile } from '../../hooks/useProfile';
import { format } from 'date-fns';

const CertificationsTab = () => {
  const {
    certifications,
    certificationsLoading,
    createCertification,
    updateCertification,
    deleteCertification,
    isCreatingCertification,
    isUpdatingCertification,
    isDeletingCertification,
  } = useProfile();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(getDefaultForm());

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData(getDefaultForm());
    setOpenDialog(true);
  };

  const handleOpenEdit = (cert) => {
    setEditingId(cert.id);
    setFormData({
      ...cert,
      issue_date: cert.issue_date ? format(new Date(cert.issue_date), 'yyyy-MM-dd') : '',
      expiry_date: cert.expiry_date ? format(new Date(cert.expiry_date), 'yyyy-MM-dd') : '',
    });
    setOpenDialog(true);
  };

  const handleClose = () => {
    setOpenDialog(false);
    setEditingId(null);
    setFormData(getDefaultForm());
  };

  const handleSave = () => {
    if (editingId) {
      updateCertification({ id: editingId, data: formData });
    } else {
      createCertification(formData);
    }
    handleClose();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this certification?')) {
      deleteCertification(id);
    }
  };

  if (certificationsLoading) {
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
          <p>Certifications</p>
        </div>
        <div className="text-blue-600">
          <button className="btn btn-info" onClick={handleOpenCreate}>
            <AddIcon />
            Add Certification
          </button>
        </div>
      </div>



      {certifications.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CertificationIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="textSecondary" sx={{ mt: 2 }}>
            No Certifications Added
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Add your certifications to boost your profile
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {certifications.map((cert) => (
            <Grid item xs={12} md={6} key={cert.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" fontWeight="bold" gutterBottom>
                        {cert.name}
                      </Typography>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        {cert.issuing_organization}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Level: {cert.level}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Issued: {cert.issue_date && format(new Date(cert.issue_date), 'MMM yyyy')}
                        {cert.is_lifetime 
                          ? ' • Lifetime' 
                          : cert.expiry_date && ` • Expires: ${format(new Date(cert.expiry_date), 'MMM yyyy')}`}
                      </Typography>
                      {cert.skills_covered?.length > 0 && (
                        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {cert.skills_covered.slice(0, 5).map((skill) => (
                            <Chip 
                              key={skill} 
                              label={skill} 
                              size="small" 
                              variant="outlined" 
                              color="primary"
                            />
                          ))}
                          {cert.skills_covered.length > 5 && (
                            <Chip 
                              label={`+${cert.skills_covered.length - 5}`} 
                              size="small" 
                              color="primary" 
                            />
                          )}
                        </Box>
                      )}
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Edit">
                        <IconButton 
                          onClick={() => handleOpenEdit(cert)} 
                          size="small" 
                          color="primary"
                          aria-label="edit certification"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          onClick={() => handleDelete(cert.id)}
                          size="small"
                          color="error"
                          disabled={isDeletingCertification}
                          aria-label="delete certification"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={handleClose} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" fontWeight="bold">
            {editingId ? 'Edit Certification' : 'Add Certification'}
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Certification Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                size="small"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Issuing Organization"
                value={formData.issuing_organization}
                onChange={(e) => setFormData({ ...formData, issuing_organization: e.target.value })}
                required
                size="small"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Level</InputLabel>
                <Select
                  value={formData.level || 'professional'}
                  onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                  label="Level"
                >
                  <MenuItem value="foundational">Foundational</MenuItem>
                  <MenuItem value="associate">Associate</MenuItem>
                  <MenuItem value="professional">Professional</MenuItem>
                  <MenuItem value="expert">Expert</MenuItem>
                  <MenuItem value="master">Master</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Credential ID"
                value={formData.credential_id}
                onChange={(e) => setFormData({ ...formData, credential_id: e.target.value })}
                size="small"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Credential URL"
                value={formData.credential_url}
                onChange={(e) => setFormData({ ...formData, credential_url: e.target.value })}
                size="small"
                variant="outlined"
                placeholder="https://..."
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Issue Date"
                type="date"
                value={formData.issue_date}
                onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                required
                InputLabelProps={{ shrink: true }}
                size="small"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Expiry Date"
                type="date"
                value={formData.expiry_date}
                onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                disabled={formData.is_lifetime}
                size="small"
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_lifetime || false}
                    onChange={(e) => setFormData({ ...formData, is_lifetime: e.target.checked })}
                    color="primary"
                  />
                }
                label="Lifetime Certification (No Expiry)"
              />
            </Grid>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={formData.skills_covered || []}
                onChange={(e, newValue) => {
                  setFormData({ ...formData, skills_covered: newValue });
                }}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => {
                    const { key, ...tagProps } = getTagProps({ index });
                    return (
                      <Chip
                        key={key || option}
                        label={option}
                        {...tagProps}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ m: 0.5 }}
                      />
                    );
                  })
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Skills Covered"
                    placeholder="Type a skill and press Enter..."
                    size="small"
                    variant="outlined"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
                size="small"
                variant="outlined"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button 
            onClick={handleClose} 
            variant="outlined"
            color="inherit"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={isCreatingCertification || isUpdatingCertification}
            startIcon={isCreatingCertification || isUpdatingCertification ? <CircularProgress size={20} /> : null}
          >
            {isCreatingCertification || isUpdatingCertification 
              ? 'Saving...' 
              : editingId 
                ? 'Update' 
                : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

function getDefaultForm() {
  return {
    name: '',
    issuing_organization: '',
    level: 'professional',
    credential_id: '',
    credential_url: '',
    issue_date: '',
    expiry_date: '',
    is_lifetime: false,
    skills_covered: [],
    description: '',
  };
}

export default CertificationsTab;