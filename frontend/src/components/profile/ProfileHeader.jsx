// frontend/src/components/profile/ProfileHeader.jsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Grid,
  Avatar,
  Typography,
  Button,
  IconButton,
  Chip,
  TextField,
  Stack,
  Tooltip,
  Badge,
  Autocomplete,
  CircularProgress,
  Divider,
} from "@mui/material";
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  PhotoCamera as PhotoCameraIcon,
  LinkedIn as LinkedInIcon,
  GitHub as GitHubIcon,
  Public as PublicIcon,
  LocationOn as LocationIcon,
} from "@mui/icons-material";
import { useAuth } from "../../hooks/useAuth";
import { color, shadows } from '@mui/system';
import BasicInfoTab from "./BasicInfoTab";

const ProfileHeader = ({ profile, onUpdate, isUpdatingProfile }) => {
  const { user } = useAuth();

  const [isEditingBasicInfo, setIsEditingBasicInfo] = useState(false);

  useEffect(() => {
    // keep existing side effects minimal; profile drives UI
  }, [profile]);

  const safeProfile = profile || {};

  return (
    <Grid container spacing={3} sx={{ bgcolor: "black", color: "white", position: "relative" }}>
      {/* Edit Button */}
      <Box sx={{ position: "absolute", top: 8, right: 8, zIndex: 2 }}>
        <IconButton
          size="small"
          sx={{
            bgcolor: "rgba(255,255,255,0.08)",
            color: "white",
            border: "1px solid rgba(255,255,255,0.15)",
            "&:hover": { bgcolor: "rgba(255,255,255,0.15)" },
          }}
          onClick={() => setIsEditingBasicInfo(true)}
          aria-label="Edit profile header"
        >
          <EditIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Avatar Section */}
      <Grid item xs={12} sm={4} md={3} sx={{ textAlign: "center" }}>
        <Badge
          overlap="circular"
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          badgeContent={
            <IconButton
              size="small"
              sx={{
                bgcolor: "primary.main",
                color: "white",
                "&:hover": { bgcolor: "primary.dark" },
              }}
            >
              <PhotoCameraIcon fontSize="small" />
            </IconButton>
          }
        >
          <Avatar
            src={safeProfile?.profile_picture}
            sx={{
              width: 70,
              height: 70,
              mx: "auto",
              fontSize: 48,
              bgcolor: "primary.main",
            }}
          >
            {safeProfile?.name?.charAt(0) || user?.name?.charAt(0) || "U"}
          </Avatar>
        </Badge>
      </Grid>

      {/* Info Section */}
      <Grid item xs={12} sm={8} md={9}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <Box sx={{ flex: 1, borderBottom: 2, borderBottomColor: "gray" }}>
            <Typography variant="h6" sx={{ mt: 1, fontWeight: "bold" }}>
              {safeProfile?.name || user?.name || "User"}
            </Typography>

            <Typography variant="body1" sx={{ mb: 2, color: "gray" }}>
              {safeProfile?.professional_summary || "No professional summary added yet."}
            </Typography>

            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 1, mb: 2 }}>
              <Typography variant="body2" sx={{ color: "#bdbdbd" }}>
                <b>Email:</b> {safeProfile?.email || user?.email || "-"}
              </Typography>
              <Typography variant="body2" sx={{ color: "#bdbdbd" }}>
                <b>Phone:</b> {safeProfile?.phone || "-"}
              </Typography>
              <Typography variant="body2" sx={{ color: "#bdbdbd" }}>
                <b>DOB:</b> {safeProfile?.dob || "-"}
              </Typography>
              <Typography variant="body2" sx={{ color: "#bdbdbd" }}>
                <b>Gender:</b> {safeProfile?.gender || "-"}
              </Typography>
              <Typography variant="body2" sx={{ color: "#bdbdbd", gridColumn: { xs: "auto", sm: "span 2" } }}>
                <b>Address:</b> {safeProfile?.address || "-"}
              </Typography>
            </Box>
          </Box>

          <Box>
            <Typography variant="body1" sx={{ mb: 2, color: "gray" }} />
          </Box>
        </Box>
      </Grid>

      {/* Edit Modal */}
      {isEditingBasicInfo && (
        <Box
          sx={{
            position: "fixed",
            inset: 0,
            bgcolor: "rgba(0,0,0,0.65)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 2,
          }}
          onClick={() => setIsEditingBasicInfo(false)}
        >
          <Box
            sx={{
              width: "100%",
              maxWidth: 720,
              maxHeight: "90vh",
              overflowY: "auto",
              bgcolor: "#121212",
              borderRadius: 2,
              border: "1px solid rgba(255,255,255,0.12)",
              p: 2,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
              <Typography sx={{ color: "white", fontWeight: 700 }}>Edit profile</Typography>
              <IconButton
                size="small"
                sx={{ color: "white", bgcolor: "rgba(255,255,255,0.08)" }}
                onClick={() => setIsEditingBasicInfo(false)}
              >
                <CancelIcon fontSize="small" />
              </IconButton>
            </Box>

            <BasicInfoTab
              profile={safeProfile}
              onUpdate={(payload) => onUpdate(payload)}
              isUpdating={isUpdatingProfile}
              hideHeaderFields
              onDone={() => setIsEditingBasicInfo(false)}
            />
          </Box>
        </Box>
      )}
    </Grid>
  );
};

export default ProfileHeader;

