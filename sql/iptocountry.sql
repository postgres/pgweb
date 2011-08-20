
CREATE TABLE iptocountry (
    id integer DEFAULT nextval(('iptocountry_id_seq'::text)::regclass) NOT NULL,
    startip bigint NOT NULL,
    endip bigint NOT NULL,
    countrycode character(2) NOT NULL,
    country character varying(100) NOT NULL
);


ALTER TABLE ONLY iptocountry
    ADD CONSTRAINT iptocountry_pkey PRIMARY KEY (id);
