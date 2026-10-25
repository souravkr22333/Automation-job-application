import React, { useState } from "react";
import axios from "axios";
import {useNavigate} from "react-router-dom";
import { jobApi } from "../../services/jobApi";


export default function UploadResume() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [file, setFile] = useState();

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] ?? null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      alert("Please select a file to upload.");
      return;
    }

    const access_token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", file.name);
    formData.append("is_default", "true");

    try {
      // Important: do NOT manually set Content-Type for FormData.
      // axios/browser will add the correct multipart boundary automatically.
      const res = await axios.post(
        'https://automation-job-application-production.up.railway.app/api/resumes/',
        //  "http://localhost:8000/api/resumes/",
        formData,
        {
          headers: {
            Authorization: `Bearer ${access_token}`,
          },
        },
      );
      if(res.statusText=="Created"){

        alert("Resume updated successfuly");
        // Trigger auto job discovery ONCE (first time only — when new user uploads resume)
        const autoDiscoverDone = localStorage.getItem('auto_discover_done');
        if (!autoDiscoverDone) {
          jobApi.autoDiscover().catch(err => {
            console.log('[AutoDiscover] Triggered after resume upload', err?.response?.status);
          });
          localStorage.setItem('auto_discover_done', 'true');
        }
        navigate("/");
        
      }
      else{
      console.log("error",res.status)
      }
      
    } catch (err) {
      console.error("Upload error:", err);
      console.log("upload failed", +err.message);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-black">
      <div className="bg-[#111111] border border-[#2A2A2A] rounded-xl p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold text-white mb-4">Upload Resume</h1>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-white mb-1">
              Select Resume File
            </label>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              className="w-full px-4 py-2 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              onChange={handleFileChange}
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Upload
          </button>

          {message && <p className="text-sm text-white mt-2">{message}</p>}
        </form>
      </div>
    </div>
  );
}
