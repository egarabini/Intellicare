import { useState } from "react";
import { notifications } from "@mantine/notifications";
import { useAuth } from "react-oidc-context";

export function useDownloadPdf() {
  const auth = useAuth();
  const [isDownloading, setIsDownloading] = useState(false);

  const downloadPdf = async (url: string, filename: string) => {
    setIsDownloading(true);
    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${auth.user?.access_token}` },
      });

      if (!res.ok) {
        throw new Error("Erro ao gerar PDF");
      }

      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      URL.revokeObjectURL(link.href);

      notifications.show({
        title: "Sucesso",
        message: "Download do PDF iniciado.",
        color: "green",
      });
    } catch (error) {
      console.error("Erro no download de PDF:", error);
      notifications.show({
        title: "Erro",
        message: "Houve um problema ao exportar o documento.",
        color: "red",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return { downloadPdf, isDownloading };
}
