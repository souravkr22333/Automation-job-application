// frontend/src/components/profile/ExperienceTab.jsx
import React, { useState } from "react";
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
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Work as WorkIcon,
} from "@mui/icons-material";
import { useProfile } from "../../hooks/useProfile";
import { format } from "date-fns";

const ExperienceTab = () => {
  const {
    experiences,
    experiencesLoading,
    createExperience,
    updateExperience,
    deleteExperience,
    isCreatingExperience,
    isUpdatingExperience,
    isDeletingExperience,
  } = useProfile();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(getDefaultForm());

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData(getDefaultForm());
    setOpenDialog(true);
  };

  const handleOpenEdit = (experience) => {
    setEditingId(experience.id);
    setFormData({
      ...experience,
      start_date: experience.start_date
        ? format(new Date(experience.start_date), "yyyy-MM-dd")
        : "",
      end_date: experience.end_date
        ? format(new Date(experience.end_date), "yyyy-MM-dd")
        : "",
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
      updateExperience({ id: editingId, data: formData });
    } else {
      createExperience(formData);
    }
    handleClose();
  };

  const handleDelete = (id) => {
    if (window.confirm("Are you sure you want to delete this experience?")) {
      deleteExperience(id);
    }
  };

  if (experiencesLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div className="bg-gray-800 p-3 pt-5 rounded-2xl">
      <div className="flex justify-between border-b w-auto mb-3">
        <div>
          <p>Work Experience</p>
        </div>
        <div className="text-blue-600">
          <button className="btn btn-info" onClick={handleOpenCreate}>
            <AddIcon />
            Add Experience
          </button>
        </div>
      </div>

      {experiences.length === 0 ? (
        <Box sx={{ textAlign: "center", py: 6 }}>
          <WorkIcon sx={{ fontSize: 64, color: "text.disabled" }} />
          <Typography variant="h6" color="textSecondary" sx={{ mt: 2 }}>
            No Experience Added
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Add your work experience to showcase your career
          </Typography>
        </Box>
      ) : (
        <div container>
          {experiences.map((exp) => (
            <div item xs={12} sm={12} md={12} lg={12} key={exp.id}>
              <div className="w-auto bg-gray-900 p-5 mb-1 flex justify-between  rounded-xl shadow-sm transform transition-all duration-300 hover:-translate-y-2 hover:shadow-xl hover:shadow-gray-500/50">
                <div>
                  <h6>{exp.company_name}</h6>
                  <p>{exp.job_title}</p>

                  <p variant="body2" color="white">
                    {exp.start_date &&
                      format(new Date(exp.start_date), "MMM yyyy")}
                    {exp.is_current
                      ? " - Present"
                      : exp.end_date &&
                        ` - ${format(new Date(exp.end_date), "MMM yyyy")}`}
                  </p>
                  {exp.description && (
                    <p variant="body2" sx={{ mt: 1 }}>
                      {exp.description}
                    </p>
                  )}
                </div>
                <div direction="row" spacing={1}>
                  <div title="Edit">
                    <div onClick={() => handleOpenEdit(exp)} size="small">
                      <EditIcon fontSize="small" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleClose} maxWidth="md" fullWidth >
        <div className="bg-gray-900 text-white">
        <div className="flex justify-between p-2">
          <div>{editingId ? "Edit Experience" : "Add Experience"}</div>
          <div>
            <div
              onClick={() => handleDelete(exp.id)}
              size="small"
              color="error"
              disabled={isDeletingExperience}
            >
              <DeleteIcon fontSize="small" sx={{ color: "red" }} />
            </div>
          </div>
        </div>
        <div className="p-5 ">
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Company Name"
                value={formData.company_name}
                onChange={(e) =>
                  setFormData({ ...formData, company_name: e.target.value })
                }
                required
                size="small"
                color="white"
                
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Job Title"
                value={formData.job_title}
                onChange={(e) =>
                  setFormData({ ...formData, job_title: e.target.value })
                }
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Employment Type</InputLabel>
                <Select
                  value={formData.employment_type || "full_time"}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employment_type: e.target.value,
                    })
                  }
                  label="Employment Type"
                >
                  <MenuItem value="full_time">Full Time</MenuItem>
                  <MenuItem value="part_time">Part Time</MenuItem>
                  <MenuItem value="contract">Contract</MenuItem>
                  <MenuItem value="internship">Internship</MenuItem>
                  <MenuItem value="freelance">Freelance</MenuItem>
                  <MenuItem value="remote">Remote</MenuItem>
                  <MenuItem value="hybrid">Hybrid</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Experience Level</InputLabel>
                <Select
                  value={formData.experience_level || "mid"}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      experience_level: e.target.value,
                    })
                  }
                  label="Experience Level"
                >
                  <MenuItem value="entry">Entry Level</MenuItem>
                  <MenuItem value="junior">Junior</MenuItem>
                  <MenuItem value="mid">Mid Level</MenuItem>
                  <MenuItem value="senior">Senior</MenuItem>
                  <MenuItem value="lead">Lead</MenuItem>
                  <MenuItem value="manager">Manager</MenuItem>
                  <MenuItem value="director">Director</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Company Location"
                value={formData.company_location}
                onChange={(e) =>
                  setFormData({ ...formData, company_location: e.target.value })
                }
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={formData.start_date}
                onChange={(e) =>
                  setFormData({ ...formData, start_date: e.target.value })
                }
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
                onChange={(e) =>
                  setFormData({ ...formData, end_date: e.target.value })
                }
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
                    onChange={(e) =>
                      setFormData({ ...formData, is_current: e.target.checked })
                    }
                  />
                }
                label="Currently Working Here"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                multiline
                rows={3}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={formData.technologies_used || []}
                onChange={(e, newValue) =>
                  setFormData({ ...formData, technologies_used: newValue })
                }
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      key={option}
                      {...getTagProps({ index })}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
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
                onChange={(e, newValue) =>
                  setFormData({ ...formData, skills_used: newValue })
                }
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      key={option}
                      {...getTagProps({ index })}
                      size="small"
                      variant="outlined"
                      color="secondary"
                    />
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
        </div>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={isCreatingExperience || isUpdatingExperience}
          >
            {isCreatingExperience || isUpdatingExperience ? (
              <CircularProgress size={24} />
            ) : editingId ? (
              "Update"
            ) : (
              "Add"
            )}
          </Button>
        </DialogActions>
        </div>
      </Dialog>
    </div>
  );
};

function getDefaultForm() {
  return {
    company_name: "",
    company_location: "",
    job_title: "",
    employment_type: "full_time",
    experience_level: "mid",
    start_date: "",
    end_date: "",
    is_current: false,
    description: "",
    achievements: [],
    technologies_used: [],
    skills_used: [],
  };
}

export default ExperienceTab;
