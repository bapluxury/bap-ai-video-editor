Bap-ai-video-editor/
├── .env.example
├── docker-compose.yml
├── README.md
├── database/
│   └── migrations/
│       └── 001_initial_schema.sql
├── backend/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── db.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── vision_adapter.py
│   │   │   ├── stt_adapter.py
│   │   │   ├── tts_adapter.py
│   │   │   ├── voice_conv_adapter.py
│   │   │   └── storage_adapter.py
│   │   ├── video_engine/
│   │   │   ├── probe.py
│   │   │   ├── analyzer.py
│   │   │   ├── reframer.py
│   │   │   ├── planner.py
│   │   │   ├── subtitles.py
│   │   │   ├── audio_mixer.py
│   │   │   └── renderer.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   └── api/
│   │       └── v1/
│   │           ├── routes_projects.py
│   │           ├── routes_videos.py
│   │           ├── routes_jobs.py
│   │           ├── routes_voice_subtitles.py
│   │           ├── routes_library_history.py
│   │           └── routes_system.py
│   └── tests/
│       ├── test_api.py
│       ├── test_planner_reframer.py
│       └── test_ffmpeg_pipeline.py
└── frontend/
    ├── Dockerfile.web
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── globals.css
    │   │   ├── page.tsx
    │   │   ├── queue/page.tsx
    │   │   ├── preview/[jobId]/page.tsx
    │   │   ├── library/page.tsx
    │   │   ├── voice/page.tsx
    │   │   ├── subtitles/page.tsx
    │   │   ├── history/page.tsx
    │   │   ├── vip/page.tsx
    │   │   └── settings/page.tsx
    │   ├── components/
    │   │   ├── Header.tsx
    │   │   ├── Navigation.tsx
    │   │   ├── VietnamIslandMap.tsx
    │   │   ├── UploadDropzone.tsx
    │   │   ├── JobProgressPanel.tsx
    │   │   ├── ThreeVersionsGrid.tsx
    │   │   └── ProviderStatusBadge.tsx
    │   └── lib/
    │       ├── api.ts
    │       └── types.ts
    └── tests/
        └── e2e.spec.ts 
-- BẮP AI VIDEO EDITOR - Initial Production Schema
-- Target: PostgreSQL 15+ / Supabase PostgreSQL

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users (maps to Supabase auth.users or standalone JWT auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'vip', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Projects
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL DEFAULT '9:16' CHECK (aspect_ratio IN ('9:16', '16:9', '1:1', '4:5')),
    target_resolution TEXT NOT NULL DEFAULT '1080p' CHECK (target_resolution IN ('720p', '1080p', '2K', '4K')),
    target_codec TEXT NOT NULL DEFAULT 'h264' CHECK (target_codec IN ('h264', 'h265')),
    music_style TEXT NOT NULL DEFAULT 'none',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'queued', 'processing', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Source Videos
CREATE TABLE IF NOT EXISTS public.source_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    duration DOUBLE PRECISION NOT NULL CHECK (duration >= 0),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    fps DOUBLE PRECISION NOT NULL DEFAULT 30.0,
    codec TEXT NOT NULL DEFAULT 'unknown',
    has_audio BOOLEAN NOT NULL DEFAULT TRUE,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    status TEXT NOT NULL DEFAULT 'validated' CHECK (status IN ('uploading', 'validated', 'invalid', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Edit Jobs
CREATE TABLE IF NOT EXISTS public.edit_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    source_video_id UUID REFERENCES public.source_videos(id) ON DELETE SET NULL,
    celery_task_id TEXT,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (
        status IN (
            'queued', 'uploading', 'probing', 'analyzing_ai', 'scene_detecting',
            'planning', 'rendering_visuals', 'processing_voice', 'generating_subtitles',
            'mixing_audio', 'exporting', 'verifying', 'completed', 'failed', 'paused', 'cancelled'
        )
    ),
    current_stage TEXT NOT NULL DEFAULT 'Đang chờ trong hàng đợi',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    requested_duration DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 5. Edit Plans (Cinematic, Dynamic, Natural)
CREATE TABLE IF NOT EXISTS public.edit_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.edit_jobs(id) ON DELETE CASCADE,
    version_type TEXT NOT NULL CHECK (version_type IN ('CINEMATIC', 'DYNAMIC', 'NATURAL')),
    editing_plan_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, version_type)
);

-- 6. Output Videos
CREATE TABLE IF NOT EXISTS public.output_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.edit_jobs(id) ON DELETE CASCADE,
    version_type TEXT NOT NULL CHECK (version_type IN ('CINEMATIC', 'DYNAMIC', 'NATURAL')),
    storage_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    source_resolution TEXT NOT NULL,
    resolution TEXT NOT NULL,
    upscaled_from_source BOOLEAN NOT NULL DEFAULT FALSE,
    codec TEXT NOT NULL,
    fps DOUBLE PRECISION NOT NULL,
    duration DOUBLE PRECISION NOT NULL,
    file_size BIGINT NOT NULL,
    ffprobe_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, version_type)
);

-- 7. Voice Settings
CREATE TABLE IF NOT EXISTS public.voice_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    voice_type TEXT NOT NULL CHECK (voice_type IN ('keep_original', 'ai_voice_conversion', 'tts_narration')),
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id)
);

-- 8. Subtitle Tracks
CREATE TABLE IF NOT EXISTS public.subtitle_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    style TEXT NOT NULL DEFAULT 'white_outline' CHECK (
        style IN ('white_outline', 'yellow_bold', 'karaoke', 'highlight', 'minimal', 'sentence')
    ),
    subtitle_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id)
);

-- 9. API Connections (NEVER stores plaintext secrets; stores encrypted_ref managed only by backend)
CREATE TABLE IF NOT EXISTS public.api_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT UNIQUE NOT NULL,
    connection_status TEXT NOT NULL DEFAULT 'unconfigured' CHECK (
        connection_status IN ('unconfigured', 'connected', 'failed')
    ),
    configuration_reference TEXT, -- Fernet-encrypted JSON payload or env reference
    last_checked_at TIMESTAMPTZ,
    last_error TEXT
);

-- 10. Activity Logs
CREATE TABLE IF NOT EXISTS public.activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_source_videos_project_id ON public.source_videos(project_id);
CREATE INDEX IF NOT EXISTS idx_edit_jobs_project_id ON public.edit_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_edit_jobs_status ON public.edit_jobs(status);
CREATE INDEX IF NOT EXISTS idx_output_videos_job_id ON public.output_videos(job_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.activity_logs(user_id, created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.edit_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.edit_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.output_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subtitle_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;

-- Policies (Supabase auth.uid() isolation; service_role bypasses RLS on backend workers)
CREATE POLICY users_self_select ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY projects_owner_all ON public.projects
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY source_videos_owner_all ON public.source_videos
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_id AND p.user_id = auth.uid())
    );

CREATE POLICY edit_jobs_owner_all ON public.edit_jobs
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_id AND p.user_id = auth.uid())
    );

CREATE POLICY edit_plans_owner_select ON public.edit_plans
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.edit_jobs j
            JOIN public.projects p ON p.id = j.project_id
            WHERE j.id = job_id AND p.user_id = auth.uid()
        )
    );

CREATE POLICY output_videos_owner_select ON public.output_videos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.edit_jobs j
            JOIN public.projects p ON p.id = j.project_id
            WHERE j.id = job_id AND p.user_id = auth.uid()
        )
    );

CREATE POLICY voice_settings_owner_all ON public.voice_settings
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_id AND p.user_id = auth.uid())
    );

CREATE POLICY subtitle_tracks_owner_all ON public.subtitle_tracks
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_id AND p.user_id = auth.uid())
    );

-- api_connections MUST NOT be readable by public/anon/authenticated frontend roles
CREATE POLICY api_connections_deny_client ON public.api_connections
    FOR ALL USING (FALSE);

CREATE POLICY activity_logs_owner_select ON public.activity_logs
    FOR SELECT USING (auth.uid() = user_id);
