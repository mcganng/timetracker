--
-- PostgreSQL database dump
--

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: timetracker
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO timetracker;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_job_codes; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.admin_job_codes (
    id integer NOT NULL,
    admin_code character varying(50) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admin_job_codes OWNER TO timetracker;

--
-- Name: admin_job_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: timetracker
--

CREATE SEQUENCE public.admin_job_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_job_codes_id_seq OWNER TO timetracker;

--
-- Name: admin_job_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: timetracker
--

ALTER SEQUENCE public.admin_job_codes_id_seq OWNED BY public.admin_job_codes.id;


--
-- Name: company_holidays; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.company_holidays (
    id integer NOT NULL,
    holiday_date date NOT NULL,
    holiday_name character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.company_holidays OWNER TO timetracker;

--
-- Name: company_holidays_id_seq; Type: SEQUENCE; Schema: public; Owner: timetracker
--

CREATE SEQUENCE public.company_holidays_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.company_holidays_id_seq OWNER TO timetracker;

--
-- Name: company_holidays_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: timetracker
--

ALTER SEQUENCE public.company_holidays_id_seq OWNED BY public.company_holidays.id;


--
-- Name: job_task_codes; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.job_task_codes (
    task_code integer NOT NULL,
    task_name character varying(100) NOT NULL,
    category character varying(20) NOT NULL,
    description text,
    is_active boolean DEFAULT true
);


ALTER TABLE public.job_task_codes OWNER TO timetracker;

--
-- Name: project_budgets; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.project_budgets (
    id integer NOT NULL,
    job_number character varying(50) NOT NULL,
    customer_name character varying(200) NOT NULL,
    project_description text,
    budget_hours numeric(10,2) NOT NULL,
    status character varying(20) DEFAULT 'Active'::character varying,
    start_date date,
    end_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);


ALTER TABLE public.project_budgets OWNER TO timetracker;

--
-- Name: project_budgets_id_seq; Type: SEQUENCE; Schema: public; Owner: timetracker
--

CREATE SEQUENCE public.project_budgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_budgets_id_seq OWNER TO timetracker;

--
-- Name: project_budgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: timetracker
--

ALTER SEQUENCE public.project_budgets_id_seq OWNED BY public.project_budgets.id;


--
-- Name: time_entries; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.time_entries (
    id integer NOT NULL,
    user_id integer,
    entry_date date NOT NULL,
    job_number character varying(50) NOT NULL,
    job_task_code integer,
    job_type character varying(50),
    description text,
    hours numeric(10,2) NOT NULL,
    category character varying(20) NOT NULL,
    customer_name character varying(200),
    job_description text,
    person_responsible character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.time_entries OWNER TO timetracker;

--
-- Name: time_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: timetracker
--

CREATE SEQUENCE public.time_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.time_entries_id_seq OWNER TO timetracker;

--
-- Name: time_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: timetracker
--

ALTER SEQUENCE public.time_entries_id_seq OWNED BY public.time_entries.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: timetracker
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    role character varying(20) DEFAULT 'user'::character varying,
    is_active boolean DEFAULT true NOT NULL,
    hire_date date,
    pto_time numeric(10,2) DEFAULT 0,
    theme character varying(10) DEFAULT 'light'::character varying NOT NULL
);


ALTER TABLE public.users OWNER TO timetracker;

--
-- Name: time_entries_with_details; Type: VIEW; Schema: public; Owner: timetracker
--

CREATE VIEW public.time_entries_with_details AS
 SELECT te.id,
    te.user_id,
    te.entry_date,
    te.job_number,
    te.job_task_code,
    jtc.task_name,
    te.job_type,
    te.hours,
    te.category,
    te.description,
    te.customer_name,
    pb.project_description AS job_description,
    te.created_at,
    te.updated_at,
    u.username,
    u.full_name
   FROM (((public.time_entries te
     LEFT JOIN public.job_task_codes jtc ON ((((te.job_task_code)::character varying)::text = ((jtc.task_code)::character varying)::text)))
     LEFT JOIN public.users u ON ((te.user_id = u.id)))
     LEFT JOIN public.project_budgets pb ON ((lower((te.job_number)::text) = lower((pb.job_number)::text))));


ALTER VIEW public.time_entries_with_details OWNER TO timetracker;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: timetracker
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO timetracker;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: timetracker
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: admin_job_codes id; Type: DEFAULT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.admin_job_codes ALTER COLUMN id SET DEFAULT nextval('public.admin_job_codes_id_seq'::regclass);


--
-- Name: company_holidays id; Type: DEFAULT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.company_holidays ALTER COLUMN id SET DEFAULT nextval('public.company_holidays_id_seq'::regclass);


--
-- Name: project_budgets id; Type: DEFAULT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.project_budgets ALTER COLUMN id SET DEFAULT nextval('public.project_budgets_id_seq'::regclass);


--
-- Name: time_entries id; Type: DEFAULT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.time_entries ALTER COLUMN id SET DEFAULT nextval('public.time_entries_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: admin_job_codes; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.admin_job_codes (id, admin_code, description, created_at) FROM stdin;
1	ADMIN-2026	Internal Admin 2026	2026-01-01 00:00:00
\.


--
-- Data for Name: company_holidays; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.company_holidays (id, holiday_date, holiday_name, description, created_at) FROM stdin;
1	2026-01-01	New Year's Day	Federal Holiday	2026-01-01 00:00:00
2	2026-05-25	Memorial Day	Federal Holiday	2026-01-01 00:00:00
3	2026-07-04	Independence Day	Federal Holiday	2026-01-01 00:00:00
4	2026-09-07	Labor Day	Federal Holiday	2026-01-01 00:00:00
5	2026-11-26	Thanksgiving Day	Federal Holiday	2026-01-01 00:00:00
6	2026-11-27	Day After Thanksgiving	Company Holiday	2026-01-01 00:00:00
7	2026-12-24	Christmas Eve	Company Holiday	2026-01-01 00:00:00
8	2026-12-25	Christmas Day	Federal Holiday	2026-01-01 00:00:00
9	2026-12-31	New Year's Eve	Company Holiday	2026-01-01 00:00:00
\.


--
-- Data for Name: job_task_codes; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.job_task_codes (task_code, task_name, category, description, is_active) FROM stdin;
110	Planning and Design	Project	Project planning and design work	t
120	Staging	Project	Equipment staging and preparation	t
130	Implementation and Deployment	Project	System implementation and deployment	t
140	Training and Knowledge Transfer	Project	User training and knowledge transfer	t
150	Documentation	Project	Project documentation	t
169	Onsite Idle	Project	Onsite idle time	t
170	Travel	Project	Travel time for projects	t
410	Regular Department Time	Admin	Regular administrative time	t
450	Training and Conference	Admin	Training and professional development	t
420	PTO	PTO	Paid time off	t
440	Holiday	Holiday	Company holiday	t
\.


--
-- Data for Name: project_budgets; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.project_budgets (id, job_number, customer_name, project_description, budget_hours, status, start_date, end_date, created_at, updated_at, user_id) FROM stdin;
\.


--
-- Data for Name: time_entries; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.time_entries (id, user_id, entry_date, job_number, job_task_code, job_type, description, hours, category, customer_name, job_description, person_responsible, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: timetracker
--

COPY public.users (id, username, email, password_hash, full_name, created_at, last_login, role, is_active) FROM stdin;
1	Admin	Admin@timetracker.com	scrypt:32768:8:1$aGst7vRzqIKwgFfJ$32c15b24455052f2ea9a4584c00f9237b29de5d30b2371476f8dcf3e5eabe8a794d2a07d9a14406b8dafe7206b1fcbadca6fec07010c5bbb39814d897464d4c7	System Administrator	2026-01-01 00:00:00	\N	admin	t
\.


--
-- Name: admin_job_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: timetracker
--

SELECT pg_catalog.setval('public.admin_job_codes_id_seq', 1, true);


--
-- Name: company_holidays_id_seq; Type: SEQUENCE SET; Schema: public; Owner: timetracker
--

SELECT pg_catalog.setval('public.company_holidays_id_seq', 9, true);


--
-- Name: project_budgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: timetracker
--

SELECT pg_catalog.setval('public.project_budgets_id_seq', 1, false);


--
-- Name: time_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: timetracker
--

SELECT pg_catalog.setval('public.time_entries_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: timetracker
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: admin_job_codes admin_job_codes_admin_code_key; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.admin_job_codes
    ADD CONSTRAINT admin_job_codes_admin_code_key UNIQUE (admin_code);


--
-- Name: admin_job_codes admin_job_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.admin_job_codes
    ADD CONSTRAINT admin_job_codes_pkey PRIMARY KEY (id);


--
-- Name: company_holidays company_holidays_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.company_holidays
    ADD CONSTRAINT company_holidays_pkey PRIMARY KEY (id);


--
-- Name: job_task_codes job_task_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.job_task_codes
    ADD CONSTRAINT job_task_codes_pkey PRIMARY KEY (task_code);


--
-- Name: project_budgets project_budgets_job_number_key; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.project_budgets
    ADD CONSTRAINT project_budgets_job_number_key UNIQUE (job_number);


--
-- Name: project_budgets project_budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.project_budgets
    ADD CONSTRAINT project_budgets_pkey PRIMARY KEY (id);


--
-- Name: time_entries time_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: users check_theme_valid; Type: CHECK CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT check_theme_valid CHECK (theme::text = ANY (ARRAY['light'::character varying, 'dark'::character varying]::text[]));


--
-- Name: idx_project_budgets_status; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_project_budgets_status ON public.project_budgets USING btree (status);


--
-- Name: idx_project_budgets_user_id; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_project_budgets_user_id ON public.project_budgets USING btree (user_id);


--
-- Name: idx_time_entries_category; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_time_entries_category ON public.time_entries USING btree (category);


--
-- Name: idx_time_entries_date; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_time_entries_date ON public.time_entries USING btree (entry_date);


--
-- Name: idx_time_entries_date_user; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_time_entries_date_user ON public.time_entries USING btree (entry_date, user_id);


--
-- Name: idx_time_entries_job; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_time_entries_job ON public.time_entries USING btree (job_number);


--
-- Name: idx_time_entries_user; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_time_entries_user ON public.time_entries USING btree (user_id);


--
-- Name: idx_users_active; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_users_active ON public.users USING btree (is_active);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_theme; Type: INDEX; Schema: public; Owner: timetracker
--

CREATE INDEX idx_users_theme ON public.users USING btree (theme);


--
-- Name: project_budgets update_project_budgets_updated_at; Type: TRIGGER; Schema: public; Owner: timetracker
--

CREATE TRIGGER update_project_budgets_updated_at BEFORE UPDATE ON public.project_budgets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: time_entries update_time_entries_updated_at; Type: TRIGGER; Schema: public; Owner: timetracker
--

CREATE TRIGGER update_time_entries_updated_at BEFORE UPDATE ON public.time_entries FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: project_budgets fk_project_budgets_user; Type: FK CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.project_budgets
    ADD CONSTRAINT fk_project_budgets_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: time_entries time_entries_job_task_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_job_task_code_fkey FOREIGN KEY (job_task_code) REFERENCES public.job_task_codes(task_code);


--
-- Name: time_entries time_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: timetracker
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--
