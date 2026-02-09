import { UserMessageProps } from "@copilotkit/react-ui";

const FILE_UPLOAD_PREFIX = "FILE_UPLOAD::";

type UserMessageContent = NonNullable<UserMessageProps["message"]>["content"];

const getTextContent = (content: UserMessageContent | undefined): string | undefined => {
  if (typeof content === "undefined") {
    return undefined;
  }

  if (typeof content === "string") {
    return content;
  }

  return (
    content
      .map((part) => {
        if (part.type === "text") {
          return part.text;
        }
        return undefined;
      })
      .filter((value): value is string => typeof value === "string" && value.length > 0)
      .join(" ")
      .trim() || undefined
  );
};

const formatFileUploadMessage = (content: string | undefined): string | undefined => {
  if (!content || !content.startsWith(FILE_UPLOAD_PREFIX)) {
    return content;
  }

  const payload = content.slice(FILE_UPLOAD_PREFIX.length).trim();
  try {
    const data = JSON.parse(payload) as { filename?: string; content_type?: string };
    const filename = data.filename ?? "uploaded file";
    const type = data.content_type ? ` (${data.content_type})` : "";
    return `Uploaded file: ${filename}${type}`;
  } catch {
    return "Uploaded file";
  }
};

export const CustomUserMessage = (props: UserMessageProps) => {
  const { message, ImageRenderer } = props;
  const isImageMessage = message && "image" in message && Boolean(message.image);

  if (isImageMessage) {
    const imageMessage = message!;
    const content = getTextContent(imageMessage?.content);

    return (
      <div className="copilotKitMessage copilotKitUserMessage">
        <ImageRenderer image={imageMessage.image!} content={content} />
      </div>
    );
  }

  const content = getTextContent(message?.content);
  const displayText = formatFileUploadMessage(content);

  return <div className="copilotKitMessage copilotKitUserMessage">{displayText}</div>;
};
