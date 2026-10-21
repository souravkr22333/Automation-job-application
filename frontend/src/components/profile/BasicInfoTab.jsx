// frontend/src/components/profile/BasicInfoTab.jsx
import React, { useEffect } from "react";

import { LocationOn as LocationIcon } from "@mui/icons-material";
import { useForm, Controller } from "react-hook-form";

const BasicInfoTab = ({
  profile,
  onUpdate,
  isUpdating,
  hideHeaderFields,
  onDone,
}) => {
  const safeProfile = profile || {};

  const { handleSubmit, reset } = useForm({
    defaultValues: {
      email: safeProfile?.email || "",
      phone: safeProfile?.phone || "",
      dob: safeProfile?.dob || "",
      address: safeProfile?.address || "",
      gender: safeProfile?.gender || "Male",
    },
  });

  useEffect(() => {
    reset({
      email: safeProfile?.email || "",
      phone: safeProfile?.phone || "",
      dob: safeProfile?.dob || "",
      address: safeProfile?.address || "",
      gender: safeProfile?.gender || "",
    });
  }, [safeProfile, reset]);

  const onSubmit = (data) => {
    // email must not be sent to backend
    const payload = {
      name: safeProfile?.name ?? "",
      phone: data.phone ?? "",
      dob: data.dob || null,
      address: data.address ?? null,
      gender: data.gender || "",
    };

    onUpdate(payload);
    if (onDone) onDone();
  };

  return (
    <div>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="sm:flex gap-5 mb-4 w-auto">
          <div className="flex flex-col gap-2 align-middle">
            <label className="text-sm text-gray-400">EMAIL</label>
            <input
              type="text"
              defaultValue={safeProfile.email}
              name="email"
              disabled
              className="bg-gray-600 text-md rounded w-80  p-1 ps-3 opacity-70 cursor-not-allowed"
            />
          </div>

          <div className="flex flex-col gap-2 align-middle">
            <label className="text-sm text-gray-400">PHONE</label>
            <input
              type="text"
              defaultValue={safeProfile.phone}
              name="phone"
              className="bg-gray-600 text-md rounded w-80  p-1 ps-3"
            />
          </div>
        </div>

        <div className="sm:flex gap-5 mb-4 w-auto">
          <div className="flex flex-col gap-2 align-middle">
            <label className="text-sm text-gray-400">DOB</label>
            <input
              type="date"
              defaultValue={safeProfile.dob || ""}
              name="dob"
              className="bg-gray-600 text-md rounded w-80  p-1 ps-3"
            />
          </div>

          <div className="flex flex-col gap-2 align-middle">
            <label className="text-sm text-gray-400">GENDER</label>
            <input
              type="text"
              defaultValue={safeProfile.gender || ""}
              name="gender"
              placeholder="male/female/Other"
              className="bg-gray-600 text-md rounded w-80  p-1 ps-3"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2 mb-4 align-middle">
          <label className="text-sm text-gray-400">ADDRESS</label>
          <input
            type="text"
            defaultValue={safeProfile.address || ""}
            name="address"
            className="bg-gray-600 text-md rounded w-auto lg:w-166  p-1 ps-3"
          />
        </div>

        <button
          type="submit"
          disabled={!!isUpdating}
          className="btn btn-success bg-blue-600"
        >
          {isUpdating ? "Saving..." : "Save Personal info"}
        </button>
      </form>
    </div>
  );
};

export default BasicInfoTab;

