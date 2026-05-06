import Foundation
import Capacitor

@objc(LocalAIPlugin)
public class LocalAIPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "LocalAIPlugin"
    public let jsName = "LocalAI"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "loadModel", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "chatCompletion", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "isModelLoaded", returnType: CAPPluginReturnPromise)
    ]

    @objc func loadModel(_ call: CAPPluginCall) {
        let modelID = call.getString("modelId") ?? "Nemotron-Mini-4B-Instruct-Q4_K_M"
        Task {
            do {
                try await LocalAIEngine.shared.loadModel(modelID: modelID)
                call.resolve([
                    "ok": true,
                    "modelId": modelID,
                    "quantization": "Q4_K_M",
                    "backend": "Metal"
                ])
            } catch {
                call.reject("Failed to load local model: \(error.localizedDescription)")
            }
        }
    }

    @objc func chatCompletion(_ call: CAPPluginCall) {
        let rawMessages = call.getArray("messages", JSObject.self) ?? []
        let temperature = call.getFloat("temperature") ?? 0.2
        let maxTokens = call.getInt("maxTokens") ?? 256

        let messages = rawMessages.compactMap { raw -> LocalAIChatMessage? in
            guard let role = raw["role"] as? String,
                  let content = raw["content"] as? String else {
                return nil
            }
            return LocalAIChatMessage(role: role, content: content)
        }

        Task {
            do {
                let request = LocalAIChatRequest(
                    messages: messages,
                    temperature: temperature,
                    maxTokens: maxTokens
                )
                let output = try await LocalAIEngine.shared.chat(request)
                call.resolve([
                    "ok": true,
                    "content": output,
                    "modelId": "Nemotron-Mini-4B-Instruct-Q4_K_M"
                ])
            } catch {
                call.reject("Local completion failed: \(error.localizedDescription)")
            }
        }
    }

    @objc func isModelLoaded(_ call: CAPPluginCall) {
        Task {
            let loaded = await LocalAIEngine.shared.isLoaded
            call.resolve(["loaded": loaded])
        }
    }
}
