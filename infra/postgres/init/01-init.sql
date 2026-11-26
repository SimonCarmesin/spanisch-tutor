-- Läuft nur beim ersten Start eines leeren Datenbankvolumens.
-- Eigene Datenbank für das Gateway (virtuelle Schlüssel, Budgets, Kosten).
CREATE DATABASE litellm;

-- Vektorerweiterung für das Grammatikwissen (ab Etappe 2).
CREATE EXTENSION IF NOT EXISTS vector;
