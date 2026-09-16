-- Job ads fetched by fetch_ad.py and the fields extracted from them.
create table public.job_ads (
  id bigint generated always as identity primary key,
  url text not null unique,
  fetched_at timestamptz not null default now(),
  raw_text text,
  company text,
  role text,
  location text,
  work_mode text check (work_mode in ('onsite', 'hybrid', 'remote')),
  salary_min integer check (salary_min >= 0),
  salary_max integer,
  salary_period text check (salary_period in ('hour', 'day', 'month', 'year')),
  salary_currency text check (salary_currency ~ '^[A-Z]{3}$'),
  seniority text check (seniority in ('graduate', 'junior', 'mid', 'senior', 'lead')),
  must_have text[] not null default '{}',
  nice_to_have text[] not null default '{}',
  extracted_by text,
  constraint salary_range check (salary_max >= salary_min)
);

-- No policies: the Data API's anon and authenticated roles can read nothing.
-- Server-side connections (postgres, service_role) bypass RLS.
alter table public.job_ads enable row level security;

comment on column public.job_ads.url is 'Canonical ad URL: tracking query strings and fragments removed.';
comment on column public.job_ads.raw_text is 'Visible page text from fetch_ad.py, the input to extraction.';
comment on column public.job_ads.salary_period is 'What salary_min/max are per. A $700 day rate and a $110,000 salary are not comparable without it.';
comment on column public.job_ads.salary_currency is 'ISO 4217 code. Ads may be from any country.';
comment on column public.job_ads.seniority is 'Stated or clearly implied by years required. Null if the ad gives no signal.';
comment on column public.job_ads.must_have is 'Required skills and technologies as short names (PHP, SQL, Azure). Not years or degrees.';
comment on column public.job_ads.nice_to_have is 'Skills the ad marks as desired, preferred or trainable.';
comment on column public.job_ads.extracted_by is 'What produced the extracted fields, e.g. claude-code:claude-opus-5 or a model id.';
