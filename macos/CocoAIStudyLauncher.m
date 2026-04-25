#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

static NSString *CocoBundleString(NSString *key, NSString *fallback) {
    id value = [[NSBundle mainBundle] objectForInfoDictionaryKey:key];
    if ([value isKindOfClass:[NSString class]] && [value length] > 0) {
        return value;
    }
    return fallback;
}

static int CocoFreePort(void) {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        return 49500;
    }

    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = 0;

    if (bind(sockfd, (struct sockaddr *)&address, sizeof(address)) != 0) {
        close(sockfd);
        return 49500;
    }

    socklen_t length = sizeof(address);
    if (getsockname(sockfd, (struct sockaddr *)&address, &length) != 0) {
        close(sockfd);
        return 49500;
    }

    int port = ntohs(address.sin_port);
    close(sockfd);
    return port > 0 ? port : 49500;
}

static BOOL CocoWaitForServer(NSURL *url, NSTimeInterval timeout) {
    NSDate *deadline = [NSDate dateWithTimeIntervalSinceNow:timeout];
    while ([[NSDate date] compare:deadline] == NSOrderedAscending) {
        @autoreleasepool {
            NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
            request.timeoutInterval = 1.0;
            NSHTTPURLResponse *response = nil;
            NSError *error = nil;
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
            [NSURLConnection sendSynchronousRequest:request returningResponse:&response error:&error];
#pragma clang diagnostic pop
            if (response && [response statusCode] < 500) {
                return YES;
            }
            [NSThread sleepForTimeInterval:0.2];
        }
    }
    return NO;
}

@interface CocoAppDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate>
@property(nonatomic, strong) NSTask *streamlitTask;
@property(nonatomic, strong) NSWindow *window;
@property(nonatomic, strong) WKWebView *webView;
@end

@implementation CocoAppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification;
    [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
    [self applyDockIcon];
    [self createWindow];
    [self startStreamlitAndLoad];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    (void)sender;
    return YES;
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    (void)sender;
    [self stopStreamlit];
    return NSTerminateNow;
}

- (void)windowWillClose:(NSNotification *)notification {
    (void)notification;
    [self stopStreamlit];
    [NSApp terminate:nil];
}

- (void)applyDockIcon {
    NSString *iconPath = [[NSBundle mainBundle] pathForResource:@"CocoAIStudy" ofType:@"icns"];
    if (!iconPath) {
        return;
    }
    NSImage *image = [[NSImage alloc] initWithContentsOfFile:iconPath];
    if (image) {
        [NSApp setApplicationIconImage:image];
    }
}

- (void)createWindow {
    NSRect frame = NSMakeRect(0, 0, 1400, 920);
    NSUInteger style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable;
    self.window = [[NSWindow alloc] initWithContentRect:frame styleMask:style backing:NSBackingStoreBuffered defer:NO];
    self.window.title = @"CocoAi Study";
    self.window.delegate = self;
    self.window.backgroundColor = [NSColor colorWithCalibratedRed:0.153 green:0.161 blue:0.204 alpha:1.0];
    self.window.minSize = NSMakeSize(980, 700);

    WKWebViewConfiguration *configuration = [[WKWebViewConfiguration alloc] init];
    self.webView = [[WKWebView alloc] initWithFrame:self.window.contentView.bounds configuration:configuration];
    self.webView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    [self.window setContentView:self.webView];
    [self.webView loadHTMLString:[self splashHTML] baseURL:nil];
    [self.window center];
}

- (NSString *)splashHTML {
    return @"<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;width:100%;height:100%;background:#272934;color:#edf2ff;font-family:-apple-system,BlinkMacSystemFont,sans-serif}body{display:grid;place-items:center}.brand{font-size:42px;font-weight:800;color:#ff9b57}.brand span{color:#7aa8ff}.sub{margin-top:12px;color:#aab4ca;font-size:14px}</style></head><body><main><div class='brand'>COCO<span>AI</span></div><div class='sub'>CocoAi Study is starting.</div></main></body></html>";
}

- (void)startStreamlitAndLoad {
    NSString *projectRoot = CocoBundleString(@"CocoProjectRoot", [[[NSBundle mainBundle] resourcePath] stringByAppendingPathComponent:@"project"]);
    NSString *pythonBin = CocoBundleString(@"CocoPythonBin", [projectRoot stringByAppendingPathComponent:@"venv_clean/bin/python"]);
    NSString *entryPath = CocoBundleString(@"CocoStreamlitEntry", [projectRoot stringByAppendingPathComponent:@"app.py"]);
    int port = CocoFreePort();
    NSString *urlText = [NSString stringWithFormat:@"http://127.0.0.1:%d", port];
    NSURL *url = [NSURL URLWithString:urlText];

    self.streamlitTask = [[NSTask alloc] init];
    self.streamlitTask.launchPath = pythonBin;
    self.streamlitTask.currentDirectoryPath = projectRoot;
    self.streamlitTask.arguments = @[
        @"-m", @"streamlit", @"run", entryPath,
        @"--server.headless", @"true",
        @"--server.address", @"127.0.0.1",
        @"--server.port", [NSString stringWithFormat:@"%d", port],
        @"--browser.gatherUsageStats", @"false"
    ];
    NSMutableDictionary *environment = [[[NSProcessInfo processInfo] environment] mutableCopy];
    NSString *path = environment[@"PATH"] ?: @"";
    environment[@"PATH"] = [@"/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" stringByAppendingFormat:@":%@", path];
    environment[@"PYTHONPATH"] = projectRoot;
    self.streamlitTask.environment = environment;
    self.streamlitTask.standardOutput = [NSFileHandle fileHandleWithNullDevice];
    self.streamlitTask.standardError = [NSFileHandle fileHandleWithNullDevice];

    NSError *launchError = nil;
    if (![self.streamlitTask launchAndReturnError:&launchError]) {
        [self showError:[launchError localizedDescription] ?: @"Could not start Streamlit."];
        return;
    }

    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        BOOL ready = CocoWaitForServer(url, 30.0);
        dispatch_async(dispatch_get_main_queue(), ^{
            if (ready) {
                [self.webView loadRequest:[NSURLRequest requestWithURL:url]];
            } else {
                [self showError:@"Streamlit server did not become ready."];
            }
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.55 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
                [self.window makeKeyAndOrderFront:nil];
                [NSApp activateIgnoringOtherApps:YES];
            });
        });
    });
}

- (void)showError:(NSString *)message {
    NSString *safe = [[message stringByReplacingOccurrencesOfString:@"&" withString:@"&amp;"] stringByReplacingOccurrencesOfString:@"<" withString:@"&lt;"];
    NSString *html = [NSString stringWithFormat:@"<!doctype html><html><body style='margin:0;background:#272934;color:#edf2ff;font-family:-apple-system;padding:32px'><h2>CocoAi Study could not start</h2><p>%@</p></body></html>", safe];
    [self.webView loadHTMLString:html baseURL:nil];
}

- (void)stopStreamlit {
    if (self.streamlitTask && [self.streamlitTask isRunning]) {
        [self.streamlitTask terminate];
    }
}

@end

int main(int argc, const char *argv[]) {
    (void)argc;
    (void)argv;
    @autoreleasepool {
        NSApplication *application = [NSApplication sharedApplication];
        CocoAppDelegate *delegate = [[CocoAppDelegate alloc] init];
        [application setDelegate:delegate];
        [application run];
    }
    return 0;
}
