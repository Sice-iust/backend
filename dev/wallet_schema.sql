-- Migration: 0001_initial --
BEGIN;
--
-- Create model UserWallet
--
CREATE TABLE "wallet_userwallet" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, "balance" numeric(12, 2) NOT NULL, "created_on" timestamp with time zone NOT NULL, "updated_at" timestamp with time zone NOT NULL, "user_id" bigint NOT NULL UNIQUE);
--
-- Create model WalletTransaction
--
CREATE TABLE "wallet_wallettransaction" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, "transaction_id" varchar(12) NOT NULL UNIQUE, "description" text NOT NULL, "status" smallint NOT NULL CHECK ("status" >= 0), "type" smallint NOT NULL CHECK ("type" >= 0), "at" timestamp with time zone NOT NULL, "value" numeric(12, 2) NOT NULL, "wallet_id" bigint NOT NULL);
--
-- Create constraint valid_balance on model userwallet
--
ALTER TABLE "wallet_userwallet" ADD CONSTRAINT "valid_balance" CHECK ("balance" >= 0);
--
-- Create constraint valid_value on model wallettransaction
--
ALTER TABLE "wallet_wallettransaction" ADD CONSTRAINT "valid_value" CHECK ("value" >= 0);
ALTER TABLE "wallet_userwallet" ADD CONSTRAINT "wallet_userwallet_user_id_dbd99364_fk_users_user_id" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "wallet_wallettransaction" ADD CONSTRAINT "wallet_wallettransac_wallet_id_b438357c_fk_wallet_us" FOREIGN KEY ("wallet_id") REFERENCES "wallet_userwallet" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "wallet_wallettransaction_transaction_id_271ed513_like" ON "wallet_wallettransaction" ("transaction_id" varchar_pattern_ops);
CREATE INDEX "wallet_wallettransaction_wallet_id_b438357c" ON "wallet_wallettransaction" ("wallet_id");
COMMIT;


