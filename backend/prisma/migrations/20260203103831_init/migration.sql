-- CreateEnum
CREATE TYPE "RequestStatus" AS ENUM ('PENDING', 'EMAIL_VERIFIED', 'IN_ANALYSIS', 'WAITING_INFO', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "RequestType" AS ENUM ('ACCESS_REQUEST', 'DATA_CORRECTION', 'TECHNICAL_SUPPORT', 'INTEGRATION_REQUEST', 'OTHER');

-- CreateEnum
CREATE TYPE "Priority" AS ENUM ('LOW', 'NORMAL', 'HIGH', 'URGENT');

-- CreateTable
CREATE TABLE "requests" (
    "id" TEXT NOT NULL,
    "protocol" TEXT NOT NULL,
    "status" "RequestStatus" NOT NULL DEFAULT 'PENDING',
    "requesterName" TEXT NOT NULL,
    "requesterEmail" TEXT NOT NULL,
    "requesterPhone" TEXT,
    "requesterDocument" TEXT,
    "cnes" TEXT NOT NULL,
    "cnpj" TEXT,
    "establishmentName" TEXT NOT NULL,
    "establishmentType" TEXT,
    "uf" TEXT NOT NULL,
    "municipality" TEXT NOT NULL,
    "address" TEXT,
    "phone" TEXT,
    "requestType" "RequestType" NOT NULL,
    "description" TEXT NOT NULL,
    "priority" "Priority" NOT NULL DEFAULT 'NORMAL',
    "emailToken" TEXT,
    "tokenExpiresAt" TIMESTAMP(3),
    "emailVerified" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "completedAt" TIMESTAMP(3),

    CONSTRAINT "requests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "request_logs" (
    "id" TEXT NOT NULL,
    "requestId" TEXT NOT NULL,
    "status" "RequestStatus" NOT NULL,
    "message" TEXT NOT NULL,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" TEXT,

    CONSTRAINT "request_logs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "requests_protocol_key" ON "requests"("protocol");

-- CreateIndex
CREATE INDEX "requests_protocol_idx" ON "requests"("protocol");

-- CreateIndex
CREATE INDEX "requests_requesterEmail_idx" ON "requests"("requesterEmail");

-- CreateIndex
CREATE INDEX "requests_cnes_idx" ON "requests"("cnes");

-- CreateIndex
CREATE INDEX "requests_status_idx" ON "requests"("status");

-- CreateIndex
CREATE INDEX "request_logs_requestId_idx" ON "request_logs"("requestId");

-- CreateIndex
CREATE INDEX "request_logs_createdAt_idx" ON "request_logs"("createdAt");

-- AddForeignKey
ALTER TABLE "request_logs" ADD CONSTRAINT "request_logs_requestId_fkey" FOREIGN KEY ("requestId") REFERENCES "requests"("id") ON DELETE CASCADE ON UPDATE CASCADE;
