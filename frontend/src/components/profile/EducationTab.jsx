// frontend/src/components/profile/EducationTab.jsx
import React, { useState, useMemo, useEffect } from "react";
import {Box,CircularProgress} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  School as SchoolIcon,
  CheckBox,
  Work as WorkIcon,
} from "@mui/icons-material";
import { useProfile } from "../../hooks/useProfile";
import { format } from "date-fns";
import { profileService } from "../../services/userdata";
import { grey } from "@mui/material/colors";

const EducationTab = () => {
  const {
    educations,
    educationsLoading,
    createEducation,
    updateEducation,
    deleteEducation,
    createEducationAsync,
    updateEducationAsync,
    deleteEducationAsync,
    isCreatingEducation,
    isUpdatingEducation,
    isDeletingEducation,
  } = useProfile();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(getDefaultForm());
  const [isChecked, setIsChecked] = useState(false);

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData(getDefaultForm());
    setOpenDialog(true);
  };

  const handleOpenEdit = (education) => {
    setEditingId(education.id);
    setFormData({
      ...education,
      start_date: education.start_date
        ? format(new Date(education.start_date), "yyyy-MM-dd")
        : "",
      end_date: education.end_date
        ? format(new Date(education.end_date), "yyyy-MM-dd")
        : "",
    });
    setOpenDialog(true);
  };

  const handleChange = (e) => {
    setIsChecked(e.target.checked);
  };

  function getDefaultForm() {
    return {
      institution_name: "",
      institution_location: "",

      degree_name: "",

      obtained_marks: "",
      max_marks: 100,

      start_date: "",
      end_date: "",
      is_current: false,

      courses: [],
    };
  }

  const handleClose = () => {
    setOpenDialog(false);
    setEditingId(null);
    setFormData(getDefaultForm());
  };

  const handleSave = async () => {
    const sanitizedPayload = {
      ...formData,
      courses:
        Array.isArray(formData.courses) ? (formData.courses[0] ?? "") : (formData.courses ?? ""),
      end_date: formData.is_current ? null : formData.end_date,
    };

    try {
      if (editingId) {
        await updateEducationAsync({ id: editingId, data: sanitizedPayload });
      } else {
        await createEducationAsync(sanitizedPayload);
      }
    } catch (e) {
      // keep the editor open on failure so user can fix inputs
      console.error(e);
      return;
    } finally {
      // only close on success
      handleClose();
    }
  };

  const handleDelete = (id) => {
    if (window.confirm("Are you sure you want to delete this education?")) {
      deleteEducation(id);
    }
  };

  if (educationsLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div className="bg-gray-800 p-3 pt-5 rounded-2xl">
      {/* Debug: dialog open state */}
      {/* <div style={{ display: 'none' }}>{String(openDialog)}</div> */}
      <div className="flex justify-between border-b w-auto mb-3">
        <div>
          <p>Education</p>
        </div>
        <div className="text-blue-600">
          <button
            className="btn btn-info "
          
            onClick={handleOpenCreate}
          ><AddIcon />
            Add Education
          </button>
        </div>
      </div>
      <div>
        {educations.length === 0 ? (
          <div style={{textAlign:"center", margin:"2rem"}}>
          <WorkIcon sx={{ fontSize: 64, color: "text.disabled" }} />
          <p  style={{paddingTop:"20px", color:"black", fontSize:"20px"}} >
            No Education Added
          </p>
          <p  style={{paddingTop:"5px", color:"black"}}>
            Add your Educations to showcase your career
          </p>
        </div>
        ) : (
          <>
            <div>
              {educations.map((edu, index) => (
                <div
                  key={index}
                  className="w-auto bg-gray-900 p-5 mb-1 flex justify-between  rounded-xl shadow-sm transform transition-all duration-300 hover:-translate-y-2 hover:shadow-xl hover:shadow-gray-500/50"
                >
                  <div>
                    <h6>
                      {edu.degree_name} 
                    </h6>
                    <p>{edu.institution_name}</p>
                    <h8 className="text-gray">
                      {edu.start_date} - {edu.end_date}{" "}
                      {edu.obtained_marks ? `Scored ${edu.obtained_marks}` : ""}
                    </h8>
                  </div>
                  <div title="Edit">
                    <div
                      onClick={() => handleOpenEdit(edu)}
                      size="small"
                      color="primary"
                      aria-label="edit education"
                    >
                      <EditIcon fontSize="small" />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div
              className="edit_education_section mt-5 absolute top-40 bg-black"
              style={{ display: openDialog ? "block" : "none" }}
            >
              
                <div
                  className="border rounded-2xl p-5 w-177 bg-gray"
                >
                  <div className=" flex justify-between">
                    <div>
                      <p>ENTRY</p>
                    </div>
                    <div>
                      <DeleteIcon onClick={handleClose} style={{ color: "gray" }} />
                    </div>
                  </div>

                    <div>
                    <div className="mt-3 mb-3 flex flex-col gap-2">
                      <label className="text-sm text-gray-400">
                        SCHOOL/INSTUTION
                      </label>
                      <input
                        type="text"
                        className="bg-gray-600 rounded `w-168` text-xl  p-1 ps-3"
                        name="institution_name"
                        value={formData.institution_name}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            institution_name: e.target.value,
                          })
                        }
                      />
                    </div>

                    <div className="mt-3 mb-3 flex flex-col gap-2">
                      <label className="text-sm text-gray-400">ADDRESS</label>
                      <input
                        type="text"
                        className="bg-gray-600 rounded `w-168` text-xl  p-1 ps-3"
                        name="educations.institution_location"
                        value={formData.institution_location}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            institution_location: e.target.value,
                          })
                        }
                      />
                    </div>

                    <div className="flex gap-4 mb-3">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400">DEGREE</label>
                        <input
                          type="text"
                          className="bg-gray-600 rounded w-82 text-xl  p-1 ps-3"
                          name="educations.degree_name"
                          value={formData.degree_name}
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            degree_name: e.target.value,
                          })
                        }
                        />
                      </div>
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400">COURSE</label>
                        <input
                          type="text"
                          name="educations.courses"
                          value={formData.courses}
                          className="bg-gray-600 rounded text-xl w-82  p-1 ps-3"
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            courses: e.target.value,
                          })
                        }
                        />
                      </div>
                    </div>

                    <div className="flex gap-4 mb-3">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400">
                          START DATE
                        </label>
                        <input
                          type="date"
                          className="bg-gray-600 text-xl rounded w-82  p-1 ps-3"
                          name="educations.start_date"
                          value={formData.start_date}
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            start_date: e.target.value,
                          })
                        }
                        />
                        <label>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={handleChange}
                            
                          />
                          Is current
                        </label>
                      </div>
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400">END DATE</label>
                        <input
                          type="date"
                          name="educations.end_date"
                          value={formData.end_date}
                          className="bg-gray-600  rounded w-82 text-xl  p-1 ps-3"
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            end_date: e.target.value,
                          })
                        }
                        />
                      </div>
                    </div>

                    <div className="flex gap-4 mb-3">
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400">
                          OBTAINED PERCENT/SGPA/CGPA
                        </label>
                        <input
                          type="text"
                          className="bg-gray-600 rounded w-82 text-xl  p-1 ps-3"
                          name="educations.obtained_marks"
                          value={formData.obtained_marks}
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            obtained_marks: e.target.value,
                          })
                        }
                        />
                      </div>
                      <div className="flex flex-col gap-2">
                        <label className="text-sm text-gray-400 ">
                          MAX MARKS
                        </label>
                        <input
                          type="text"
                          name="educations.max_marks"
                          value={formData.max_marks}
                          className="bg-gray-600 rounded w-82 text-xl  p-1 ps-3"
                          onChange={(e) =>
                          setFormData({
                            ...formData,
                            max_marks: e.target.value,
                          })
                        }
                        />
                      </div>
                    </div>

                    <div>
                      <button onClick={handleSave} className="btn btn-success bg-blue-600">
                        Save Education Detail
                      </button>
                    </div>
                  </div>
                </div>
              
            </div>
          </>
        )}
      </div>
    </div>
     
  );
};


export default EducationTab;
