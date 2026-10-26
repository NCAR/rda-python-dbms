# rda_python_dbms

RDA Python package to manage RDA PostgreSQL databases.

## Programs

The package installs the following command-line utilities, all running as the
current user:

- `pgddl` — create, drop or alter tables, indexes and keys from the table
  definitions in `<tablename>.json` files
- `pgseq` — reset the sequences of all (or the given) tables in one or more
  schemas
- `pgbackup` — dump the configured `rdadb` schemas on `rda-pgdb-02` into
  `/data/pgbackup`, replacing existing backups and emailing a summary
- `pgdbdump` — dump a PostgreSQL database to a local directory
- `pgdbrestore` — restore a PostgreSQL database from a local dump directory
- `pgchksum` — re-check the checksums, sizes and timestamps of archived Web,
  Saved and Quasar backup files against their RDADB records, optionally fix
  the records (`-x`), and email each dataset's primary owner a list of its
  missing files (`-e`)
- `pgcmptables` — compare the columns, indexes and data of identical tables
  on two database servers
- `pgschema` — copy the tables of a schema into the same schema in another
  database on the same server

Run a program without its required options to print its usage. Do not use
`-h` for help: it is the host name option in several programs. `pgbackup`
has no usage text and starts the backup as soon as it runs.

## Environment setup

Create a Python environment first; package installs in the next section run
inside whichever environment you activate here.

### Option A — Python venv (DECS machines)

```bash
python3 -m venv $ENVHOME          # e.g. /glade/u/home/gdexdata/gdexmsenv
source $ENVHOME/bin/activate
```

### Option B — Conda (DAV/Casper)

```bash
conda create --prefix $ENVHOME python=3.12   # e.g. /glade/work/gdexdata/conda-envs/pg-gdex
conda activate $ENVHOME
```

## Installing rda-python-dbms

Pick whichever install mode fits your workflow.  All variants pull in the
transitive dependency (`rda_python_common`) automatically.

For local development, clone this repo alongside your project and install it
in editable mode so that changes are picked up without re-installing:

```bash
git clone https://github.com/NCAR/rda-python-dbms.git
cd rda-python-dbms
pip install -e .
```

To test a specific branch (e.g. an in-progress feature or fix branch), pass
`-b/--branch` to `git clone`:

```bash
git clone -b <branch-name> https://github.com/NCAR/rda-python-dbms.git
cd rda-python-dbms
pip install -e .
```

For a regular (non-editable) install from a checkout:

```bash
pip install /path/to/rda-python-dbms
```

For a production install on a system that uses the published distribution:

```bash
pip install rda_python_dbms
```
