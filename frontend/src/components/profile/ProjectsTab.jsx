// frontend/src/components/profile/ProjectsTab.jsx
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
  Code as CodeIcon,
} from '@mui/icons-material';
import { useProfile } from '../../hooks/useProfile';
import { format } from 'date-fns';

const ProjectsTab = () => {
  const {
    projects,
    projectsLoading,
    createProject,
    updateProject,
    deleteProject,
    isCreatingProject,
    isUpdatingProject,
    isDeletingProject,
  } = useProfile();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(getDefaultForm());

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData(getDefaultForm());
    setOpenDialog(true);
  };

  const handleOpenEdit = (project) => {
    setEditingId(project.id);
    setFormData({
      ...project,
      start_date: project.start_date ? format(new Date(project.start_date), 'yyyy-MM-dd') : '',
      end_date: project.end_date ? format(new Date(project.end_date), 'yyyy-MM-dd') : '',
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
      updateProject({ id: editingId, data: formData });
    } else {
      createProject(formData);
    }
    handleClose();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      deleteProject(id);
    }
  };

  if (projectsLoading) {
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
          <p>Projects</p>
        </div>
        <div className="text-blue-600">
          <button className="btn btn-info" onClick={handleOpenCreate}>
            <AddIcon />
            Add Project
          </button>
        </div>
      </div>



      {projects.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CodeIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="textSecondary" sx={{ mt: 2 }}>
            No Projects Added
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Add your projects to showcase your work
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {projects.map((project) => (
            <Grid item xs={12} md={6} key={project.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="h6" fontWeight="bold">
                        {project.name}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5, mb: 1 }}>
                        <Chip label={project.project_type} size="small" color="primary" variant="outlined" />
                        <Chip 
                          label={project.status} 
                          size="small" 
                          color={project.status === 'completed' ? 'success' : 'warning'} 
                        />
                        {project.team_size > 1 && (
                          <Chip label={`Team: ${project.team_size}`} size="small" />
                        )}
                      </Box>
                      {project.description && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {project.description}
                        </Typography>
                      )}
                      {project.technologies?.length > 0 && (
                        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {project.technologies.slice(0, 5).map((tech) => (
                            <Chip key={tech} label={tech} size="small" variant="outlined" />
                          ))}
                          {project.technologies.length > 5 && (
                            <Chip label={`+${project.technologies.length - 5}`} size="small" />
                          )}
                        </Box>
                      )}
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Edit">
                        <IconButton onClick={() => handleOpenEdit(project)} size="small" color="primary">
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          onClick={() => handleDelete(project.id)}
                          size="small"
                          color="error"
                          disabled={isDeletingProject}
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
      <Dialog open={openDialog} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingId ? 'Edit Project' : 'Add Project'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Project Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Project Type</InputLabel>
                <Select
                  value={formData.project_type || 'personal'}
                  onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                  label="Project Type"
                >
                  <MenuItem value="personal">Personal</MenuItem>
                  <MenuItem value="professional">Professional</MenuItem>
                  <MenuItem value="academic">Academic</MenuItem>
                  <MenuItem value="open_source">Open Source</MenuItem>
                  <MenuItem value="freelance">Freelance</MenuItem>
                  <MenuItem value="hackathon">Hackathon</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status || 'completed'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  label="Status"
                >
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="planned">Planned</MenuItem>
                  <MenuItem value="on_hold">On Hold</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Long Description"
                value={formData.long_description}
                onChange={(e) => setFormData({ ...formData, long_description: e.target.value })}
                multiline
                rows={3}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Project URL"
                value={formData.project_url}
                onChange={(e) => setFormData({ ...formData, project_url: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="GitHub URL"
                value={formData.github_url}
                onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Demo URL"
                value={formData.demo_url}
                onChange={(e) => setFormData({ ...formData, demo_url: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                required
                InputLabelProps={{ shrink: true }}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                disabled={formData.is_current}
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_current || false}
                    onChange={(e) => setFormData({ ...formData, is_current: e.target.checked })}
                  />
                }
                label="Currently Working On This"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Team Size"
                type="number"
                value={formData.team_size || 1}
                onChange={(e) => setFormData({ ...formData, team_size: parseInt(e.target.value) })}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Your Role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={formData.technologies || []}
                onChange={(e, newValue) => setFormData({ ...formData, technologies: newValue })}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip label={option} {...getTagProps({ index })} />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Technologies Used"
                    placeholder="Add a technology..."
                    size="small"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={formData.skills_used || []}
                onChange={(e, newValue) => setFormData({ ...formData, skills_used: newValue })}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip label={option} color="primary" variant="outlined" {...getTagProps({ index })} />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Skills Used"
                    placeholder="Add a skill..."
                    size="small"
                  />
                )}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={isCreatingProject || isUpdatingProject}
          >
            {isCreatingProject || isUpdatingProject ? (
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

function getDefaultForm() {
  return {
    name: '',
    project_type: 'personal',
    status: 'completed',
    description: '',
    long_description: '',
    technologies: [],
    skills_used: [],
    project_url: '',
    github_url: '',
    demo_url: '',
    start_date: '',
    end_date: '',
    is_current: false,
    team_size: 1,
    team_members: [],
    role: '',
    achievements: [],
    challenges: '',
    learnings: '',
  };
}

export default ProjectsTab;