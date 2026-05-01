#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#import <CoreServices/CoreServices.h>
#import <ImageIO/ImageIO.h>
#include <arpa/inet.h>
#include <dlfcn.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

static NSString * const CocoWindowFrameDefaultsKey = @"CocoAIStudyMainWindowFrameV3";
static NSString * const CocoLegacyWindowContentRectDefaultsKey = @"CocoAIStudyMainWindowContentRectV2";
static NSString * const CocoLegacyWindowFrameDefaultsKey = @"CocoAIStudyMainWindowFrame";
static const CGFloat CocoWindowDefaultWidth = 1400.0;
static const CGFloat CocoWindowDefaultHeight = 920.0;
static const CGFloat CocoWindowMinWidth = 980.0;
static const CGFloat CocoWindowMinHeight = 700.0;
static NSString * const CocoCapturePermissionUserMessage = @"화면 캡처 권한이 필요합니다. 시스템 설정에서 화면 기록 권한을 허용한 뒤 CocoAi Study를 완전히 종료하고 다시 실행해주세요.";
static NSString * const CocoCaptureFailureUserMessage = @"캡처가 취소되었거나 완료되지 않았습니다.";

static NSString *CocoBundleString(NSString *key, NSString *fallback) {
    id value = [[NSBundle mainBundle] objectForInfoDictionaryKey:key];
    if ([value isKindOfClass:[NSString class]] && [value length] > 0) {
        return value;
    }
    return fallback;
}

typedef void (^CocoCaptureCompletion)(NSRect rect, BOOL cancelled);

@interface CocoCaptureSelectionView : NSView
@property(nonatomic, copy) CocoCaptureCompletion completion;
@property(nonatomic, assign) NSPoint startPoint;
@property(nonatomic, assign) NSPoint currentPoint;
@property(nonatomic, assign) BOOL dragging;
@end

@implementation CocoCaptureSelectionView

- (BOOL)acceptsFirstResponder {
    return YES;
}

- (void)drawRect:(NSRect)dirtyRect {
    (void)dirtyRect;
    [[NSColor colorWithCalibratedWhite:0.0 alpha:0.28] setFill];
    NSRectFill(self.bounds);
    if (!self.dragging) {
        NSDictionary *attrs = @{
            NSForegroundColorAttributeName: [NSColor whiteColor],
            NSFontAttributeName: [NSFont systemFontOfSize:18 weight:NSFontWeightSemibold]
        };
        NSString *guide = @"드래그해서 캡처할 영역을 선택하세요";
        NSSize size = [guide sizeWithAttributes:attrs];
        NSPoint point = NSMakePoint(NSMidX(self.bounds) - size.width / 2.0, NSMidY(self.bounds) - size.height / 2.0);
        [guide drawAtPoint:point withAttributes:attrs];
        return;
    }

    NSRect selection = NSMakeRect(
        MIN(self.startPoint.x, self.currentPoint.x),
        MIN(self.startPoint.y, self.currentPoint.y),
        fabs(self.currentPoint.x - self.startPoint.x),
        fabs(self.currentPoint.y - self.startPoint.y)
    );
    [[NSColor colorWithCalibratedWhite:1.0 alpha:0.16] setFill];
    NSRectFill(selection);
    [[NSColor colorWithCalibratedRed:0.58 green:0.77 blue:1.0 alpha:0.95] setStroke];
    NSBezierPath *path = [NSBezierPath bezierPathWithRect:selection];
    [path setLineWidth:2.0];
    [path stroke];
}

- (void)mouseDown:(NSEvent *)event {
    self.dragging = YES;
    self.startPoint = [self convertPoint:[event locationInWindow] fromView:nil];
    self.currentPoint = self.startPoint;
    [self setNeedsDisplay:YES];
}

- (void)mouseDragged:(NSEvent *)event {
    self.currentPoint = [self convertPoint:[event locationInWindow] fromView:nil];
    [self setNeedsDisplay:YES];
}

- (void)mouseUp:(NSEvent *)event {
    self.currentPoint = [self convertPoint:[event locationInWindow] fromView:nil];
    NSRect rect = NSMakeRect(
        MIN(self.startPoint.x, self.currentPoint.x),
        MIN(self.startPoint.y, self.currentPoint.y),
        fabs(self.currentPoint.x - self.startPoint.x),
        fabs(self.currentPoint.y - self.startPoint.y)
    );
    BOOL cancelled = rect.size.width < 8.0 || rect.size.height < 8.0;
    if (self.completion) {
        self.completion(rect, cancelled);
    }
}

- (void)keyDown:(NSEvent *)event {
    if ([[event charactersIgnoringModifiers] isEqualToString:@"\033"]) {
        if (self.completion) {
            self.completion(NSZeroRect, YES);
        }
        return;
    }
    [super keyDown:event];
}

@end

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
@property(nonatomic, strong) NSTimer *captureBridgeTimer;
@property(nonatomic, assign) BOOL captureBridgeBusy;
@property(nonatomic, assign) BOOL permissionAlertShowing;
@property(nonatomic, assign) BOOL permissionDeniedAlertShownThisLaunch;
@property(nonatomic, assign) BOOL screenCapturePermissionRequestedThisLaunch;
@property(nonatomic, strong) NSMutableArray<NSWindow *> *captureOverlayWindows;
@end

@implementation CocoAppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification;
    [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
    [self applyDockIcon];
    [self createWindow];
    [self startCaptureBridge];
    [self startStreamlitAndLoad];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    (void)sender;
    return YES;
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    (void)sender;
    [self saveWindowFrame];
    [self stopStreamlit];
    return NSTerminateNow;
}

- (void)windowWillClose:(NSNotification *)notification {
    (void)notification;
    [self saveWindowFrame];
    [self stopCaptureBridge];
    [self stopStreamlit];
    [NSApp terminate:nil];
}

- (void)windowDidMove:(NSNotification *)notification {
    (void)notification;
    [self saveWindowFrame];
}

- (void)windowDidResize:(NSNotification *)notification {
    (void)notification;
    [self saveWindowFrame];
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

- (NSRect)defaultWindowContentRect {
    NSScreen *screen = [NSScreen mainScreen] ?: [[NSScreen screens] firstObject];
    if (!screen) {
        return NSMakeRect(0, 0, CocoWindowDefaultWidth, CocoWindowDefaultHeight);
    }

    NSRect visible = [screen visibleFrame];
    CGFloat width = MIN(CocoWindowDefaultWidth, MAX(CocoWindowMinWidth, visible.size.width - 80.0));
    CGFloat height = MIN(CocoWindowDefaultHeight, MAX(CocoWindowMinHeight, visible.size.height - 80.0));
    CGFloat x = NSMidX(visible) - (width / 2.0);
    CGFloat y = NSMidY(visible) - (height / 2.0);
    return NSMakeRect(round(x), round(y), round(width), round(height));
}

- (NSRect)minimumWindowFrameForStyleMask:(NSUInteger)styleMask {
    NSRect minContentRect = NSMakeRect(0, 0, CocoWindowMinWidth, CocoWindowMinHeight);
    return [NSWindow frameRectForContentRect:minContentRect styleMask:styleMask];
}

- (NSRect)defaultWindowFrameForStyleMask:(NSUInteger)styleMask {
    return [NSWindow frameRectForContentRect:[self defaultWindowContentRect] styleMask:styleMask];
}

- (BOOL)windowFrameIsVisible:(NSRect)frameRect styleMask:(NSUInteger)styleMask {
    NSRect minFrame = [self minimumWindowFrameForStyleMask:styleMask];
    if (frameRect.size.width < minFrame.size.width || frameRect.size.height < minFrame.size.height) {
        return NO;
    }

    for (NSScreen *screen in [NSScreen screens]) {
        NSRect visible = [screen visibleFrame];
        NSRect intersection = NSIntersectionRect(frameRect, visible);
        CGFloat requiredWidth = MIN(220.0, frameRect.size.width * 0.25);
        CGFloat requiredHeight = MIN(160.0, frameRect.size.height * 0.25);
        if (intersection.size.width >= requiredWidth && intersection.size.height >= requiredHeight) {
            return YES;
        }
    }
    return NO;
}

- (NSRect)restoredWindowFrameForStyleMask:(NSUInteger)styleMask {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    NSRect minFrame = [self minimumWindowFrameForStyleMask:styleMask];

    NSString *savedFrame = [defaults stringForKey:CocoWindowFrameDefaultsKey];
    if ([savedFrame length] > 0) {
        NSRect frameRect = NSRectFromString(savedFrame);
        frameRect.size.width = MAX(frameRect.size.width, minFrame.size.width);
        frameRect.size.height = MAX(frameRect.size.height, minFrame.size.height);
        if ([self windowFrameIsVisible:frameRect styleMask:styleMask]) {
            return frameRect;
        }
    }

    NSString *savedContentRect = [defaults stringForKey:CocoLegacyWindowContentRectDefaultsKey];
    if ([savedContentRect length] > 0) {
        NSRect contentRect = NSRectFromString(savedContentRect);
        contentRect.size.width = MAX(contentRect.size.width, CocoWindowMinWidth);
        contentRect.size.height = MAX(contentRect.size.height, CocoWindowMinHeight);
        NSRect frameRect = [NSWindow frameRectForContentRect:contentRect styleMask:styleMask];
        if ([self windowFrameIsVisible:frameRect styleMask:styleMask]) {
            return frameRect;
        }
    }
    return [self defaultWindowFrameForStyleMask:styleMask];
}

- (void)saveWindowFrame {
    if (!self.window) {
        return;
    }
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    [defaults setObject:NSStringFromRect([self.window frame]) forKey:CocoWindowFrameDefaultsKey];
    [defaults removeObjectForKey:CocoLegacyWindowContentRectDefaultsKey];
    [defaults removeObjectForKey:CocoLegacyWindowFrameDefaultsKey];
    [defaults synchronize];
}

- (void)createWindow {
    NSUInteger style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable;
    NSRect frameRect = [self restoredWindowFrameForStyleMask:style];
    NSRect contentRect = [NSWindow contentRectForFrameRect:frameRect styleMask:style];
    self.window = [[NSWindow alloc] initWithContentRect:contentRect styleMask:style backing:NSBackingStoreBuffered defer:NO];
    [self.window setFrame:frameRect display:NO];
    self.window.title = @"CocoAi Study";
    self.window.delegate = self;
    self.window.backgroundColor = [NSColor colorWithCalibratedRed:0.153 green:0.161 blue:0.204 alpha:1.0];
    self.window.minSize = NSMakeSize(CocoWindowMinWidth, CocoWindowMinHeight);

    WKWebViewConfiguration *configuration = [[WKWebViewConfiguration alloc] init];
    self.webView = [[WKWebView alloc] initWithFrame:self.window.contentView.bounds configuration:configuration];
    self.webView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    [self.window setContentView:self.webView];
    [self.webView loadHTMLString:[self splashHTML] baseURL:nil];
}

- (NSString *)cocoApplicationSupportPath {
    NSArray<NSString *> *paths = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES);
    NSString *base = [paths firstObject] ?: [NSTemporaryDirectory() stringByDeletingLastPathComponent];
    NSString *supportPath = [base stringByAppendingPathComponent:@"CocoAIStudy"];
    [[NSFileManager defaultManager] createDirectoryAtPath:supportPath withIntermediateDirectories:YES attributes:nil error:nil];
    return supportPath;
}

- (NSString *)captureRequestsPath {
    NSString *path = [[self cocoApplicationSupportPath] stringByAppendingPathComponent:@"native_capture_requests"];
    [[NSFileManager defaultManager] createDirectoryAtPath:path withIntermediateDirectories:YES attributes:nil error:nil];
    return path;
}

- (NSString *)captureResultsPath {
    NSString *path = [[self cocoApplicationSupportPath] stringByAppendingPathComponent:@"native_capture_results"];
    [[NSFileManager defaultManager] createDirectoryAtPath:path withIntermediateDirectories:YES attributes:nil error:nil];
    return path;
}

- (NSString *)capturesPath {
    NSString *path = [[self cocoApplicationSupportPath] stringByAppendingPathComponent:@"captures"];
    [[NSFileManager defaultManager] createDirectoryAtPath:path withIntermediateDirectories:YES attributes:nil error:nil];
    return path;
}

- (void)appendCaptureBridgeLog:(NSString *)message {
    NSString *logPath = [[self cocoApplicationSupportPath] stringByAppendingPathComponent:@"native_capture_bridge.log"];
    NSString *line = [NSString stringWithFormat:@"%@ %@\n", [NSDate date], message ?: @""];
    NSData *data = [line dataUsingEncoding:NSUTF8StringEncoding];
    if (![[NSFileManager defaultManager] fileExistsAtPath:logPath]) {
        [data writeToFile:logPath atomically:YES];
        return;
    }
    NSFileHandle *handle = [NSFileHandle fileHandleForWritingAtPath:logPath];
    [handle seekToEndOfFile];
    [handle writeData:data];
    [handle closeFile];
}

- (void)startCaptureBridge {
    [self stopCaptureBridge];
    self.captureBridgeBusy = NO;
    self.captureBridgeTimer = [NSTimer scheduledTimerWithTimeInterval:0.35 target:self selector:@selector(pollCaptureBridge:) userInfo:nil repeats:YES];
    [self appendCaptureBridgeLog:@"capture bridge started"];
}

- (void)stopCaptureBridge {
    [self.captureBridgeTimer invalidate];
    self.captureBridgeTimer = nil;
}

- (void)pollCaptureBridge:(NSTimer *)timer {
    (void)timer;
    if (self.captureBridgeBusy) {
        return;
    }

    NSString *requestsPath = [self captureRequestsPath];
    NSArray<NSString *> *entries = [[NSFileManager defaultManager] contentsOfDirectoryAtPath:requestsPath error:nil];
    NSMutableArray<NSString *> *requestFiles = [NSMutableArray array];
    for (NSString *entry in entries) {
        if ([[entry pathExtension] isEqualToString:@"json"]) {
            [requestFiles addObject:entry];
        }
    }
    if ([requestFiles count] == 0) {
        return;
    }
    [requestFiles sortUsingSelector:@selector(localizedStandardCompare:)];
    NSString *requestPath = [requestsPath stringByAppendingPathComponent:[requestFiles firstObject]];
    [self appendCaptureBridgeLog:[NSString stringWithFormat:@"capture request detected %@", [requestPath lastPathComponent]]];
    [self handleCaptureRequestAtPath:requestPath];
}

- (void)writeCaptureResult:(NSDictionary *)result requestID:(NSString *)requestID {
    NSString *resultPath = [[self captureResultsPath] stringByAppendingPathComponent:[NSString stringWithFormat:@"%@.json", requestID]];
    NSData *data = [NSJSONSerialization dataWithJSONObject:result options:0 error:nil];
    [data writeToFile:resultPath atomically:YES];
}

- (NSRect)combinedScreenFrame {
    NSRect combined = NSZeroRect;
    for (NSScreen *screen in [NSScreen screens]) {
        combined = NSEqualRects(combined, NSZeroRect) ? [screen frame] : NSUnionRect(combined, [screen frame]);
    }
    return NSEqualRects(combined, NSZeroRect) ? NSMakeRect(0, 0, 1, 1) : combined;
}

- (void)showCaptureOverlayWithCompletion:(void (^)(NSRect screenRect, BOOL cancelled))completion {
    self.captureOverlayWindows = [NSMutableArray array];
    __block BOOL completed = NO;

    for (NSScreen *screen in [NSScreen screens]) {
        NSRect frame = [screen frame];
        NSWindow *overlay = [[NSWindow alloc] initWithContentRect:frame
                                                        styleMask:NSWindowStyleMaskBorderless
                                                          backing:NSBackingStoreBuffered
                                                            defer:NO];
        overlay.level = NSScreenSaverWindowLevel;
        overlay.opaque = NO;
        overlay.backgroundColor = [NSColor clearColor];
        overlay.ignoresMouseEvents = NO;
        overlay.collectionBehavior = NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary;

        CocoCaptureSelectionView *view = [[CocoCaptureSelectionView alloc] initWithFrame:NSMakeRect(0, 0, frame.size.width, frame.size.height)];
        view.completion = ^(NSRect rect, BOOL cancelled) {
            if (completed) {
                return;
            }
            completed = YES;
            NSRect screenRect = NSMakeRect(frame.origin.x + rect.origin.x, frame.origin.y + rect.origin.y, rect.size.width, rect.size.height);
            for (NSWindow *window in self.captureOverlayWindows) {
                [window orderOut:nil];
            }
            self.captureOverlayWindows = nil;
            if (completion) {
                dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.10 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
                    completion(screenRect, cancelled);
                });
            }
        };
        overlay.contentView = view;
        [self.captureOverlayWindows addObject:overlay];
        [overlay makeKeyAndOrderFront:nil];
        [overlay makeFirstResponder:view];
    }

    [NSApp activateIgnoringOtherApps:YES];
}

- (NSArray<NSString *> *)screencaptureRectArgumentsForScreenRect:(NSRect)screenRect outputPath:(NSString *)outputPath {
    NSScreen *mainScreen = [NSScreen mainScreen] ?: [[NSScreen screens] firstObject];
    NSRect reference = mainScreen ? [mainScreen frame] : [self combinedScreenFrame];
    CGFloat x = screenRect.origin.x - reference.origin.x;
    CGFloat y = NSMaxY(reference) - NSMaxY(screenRect);
    NSString *rect = [NSString stringWithFormat:@"%ld,%ld,%ld,%ld",
                      lround(MAX(0.0, x)),
                      lround(MAX(0.0, y)),
                      lround(screenRect.size.width),
                      lround(screenRect.size.height)];
    return @[@"-x", @"-R", rect, outputPath];
}

- (BOOL)writeCGImage:(CGImageRef)image toPNGPath:(NSString *)outputPath errorMessage:(NSString **)errorMessage {
    if (!image) {
        if (errorMessage) {
            *errorMessage = @"CGImage capture returned empty image.";
        }
        return NO;
    }
    NSURL *url = [NSURL fileURLWithPath:outputPath];
    CGImageDestinationRef destination = CGImageDestinationCreateWithURL((__bridge CFURLRef)url, kUTTypePNG, 1, NULL);
    if (!destination) {
        if (errorMessage) {
            *errorMessage = @"Could not create PNG destination.";
        }
        return NO;
    }
    CGImageDestinationAddImage(destination, image, NULL);
    BOOL ok = CGImageDestinationFinalize(destination);
    CFRelease(destination);
    if (!ok && errorMessage) {
        *errorMessage = @"Could not write PNG capture file.";
    }
    return ok;
}

- (BOOL)screenCaptureAccessGranted {
    typedef bool (*CocoCGPreflightScreenCaptureAccessFunc)(void);
    CocoCGPreflightScreenCaptureAccessFunc preflight = (CocoCGPreflightScreenCaptureAccessFunc)dlsym(RTLD_DEFAULT, "CGPreflightScreenCaptureAccess");
    if (!preflight) {
        [self appendCaptureBridgeLog:@"capture permission preflight API unavailable"];
        return YES;
    }
    return preflight() ? YES : NO;
}

- (BOOL)requestScreenCaptureAccess {
    typedef bool (*CocoCGRequestScreenCaptureAccessFunc)(void);
    CocoCGRequestScreenCaptureAccessFunc request = (CocoCGRequestScreenCaptureAccessFunc)dlsym(RTLD_DEFAULT, "CGRequestScreenCaptureAccess");
    if (!request) {
        [self appendCaptureBridgeLog:@"capture permission request API unavailable"];
        return [self screenCaptureAccessGranted];
    }
    return request() ? YES : [self screenCaptureAccessGranted];
}

- (void)openScreenCapturePrivacySettings {
    NSArray<NSString *> *urls = @[
        @"x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        @"x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture"
    ];
    for (NSString *urlText in urls) {
        NSURL *url = [NSURL URLWithString:urlText];
        if (url && [[NSWorkspace sharedWorkspace] openURL:url]) {
            return;
        }
    }
}

- (void)showScreenCapturePermissionAlert {
    if (self.permissionAlertShowing || self.permissionDeniedAlertShownThisLaunch) {
        return;
    }
    self.permissionAlertShowing = YES;
    self.permissionDeniedAlertShownThisLaunch = YES;
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"화면 캡처 권한이 필요합니다.";
    alert.informativeText = @"CocoAi Study가 화면에서 선택한 문제 이미지를 읽으려면 화면 기록 권한이 필요합니다. 시스템 설정에서 CocoAi Study를 허용한 뒤 앱을 완전히 종료하고 다시 실행해주세요.";
    [alert addButtonWithTitle:@"시스템 설정 열기"];
    [alert addButtonWithTitle:@"나중에"];
    NSModalResponse response = [alert runModal];
    if (response == NSAlertFirstButtonReturn) {
        [self openScreenCapturePrivacySettings];
    }
    self.permissionAlertShowing = NO;
}

- (void)showScreenCaptureRestartAlert {
    if (self.permissionAlertShowing) {
        return;
    }
    self.permissionAlertShowing = YES;
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"CocoAi Study를 다시 실행해주세요.";
    alert.informativeText = @"화면 기록 권한 변경사항을 적용하려면 CocoAi Study를 완전히 종료한 뒤 다시 실행해야 합니다.";
    [alert addButtonWithTitle:@"확인"];
    [alert runModal];
    self.permissionAlertShowing = NO;
}

- (BOOL)ensureScreenCaptureAccess {
    if ([self screenCaptureAccessGranted]) {
        [self appendCaptureBridgeLog:@"capture permission preflight ok"];
        return YES;
    }

    if (!self.screenCapturePermissionRequestedThisLaunch) {
        self.screenCapturePermissionRequestedThisLaunch = YES;
        [self appendCaptureBridgeLog:@"capture permission preflight denied; requesting once"];
        if ([self requestScreenCaptureAccess] && [self screenCaptureAccessGranted]) {
            [self appendCaptureBridgeLog:@"capture permission request ok; restart required"];
            [self showScreenCaptureRestartAlert];
            return NO;
        }
    } else {
        [self appendCaptureBridgeLog:@"capture permission preflight denied; request already shown this launch"];
    }

    [self appendCaptureBridgeLog:@"capture permission denied after request"];
    if (!self.permissionDeniedAlertShownThisLaunch) {
        [self showScreenCapturePermissionAlert];
    }
    return NO;
}

- (BOOL)captureScreenInteractivelyToPath:(NSString *)outputPath returnCode:(int *)returnCode errorMessage:(NSString **)errorMessage {
    NSTask *task = [[NSTask alloc] init];
    task.launchPath = @"/usr/sbin/screencapture";
    task.arguments = @[@"-i", @"-x", @"-t", @"png", outputPath];

    NSPipe *errorPipe = [NSPipe pipe];
    task.standardError = errorPipe;

    @try {
        [task launch];
        [task waitUntilExit];
    } @catch (NSException *exception) {
        if (returnCode) {
            *returnCode = 1;
        }
        if (errorMessage) {
            *errorMessage = [NSString stringWithFormat:@"Could not start macOS screen capture: %@", exception.reason ?: @"unknown error"];
        }
        return NO;
    }

    int code = [task terminationStatus];
    if (returnCode) {
        *returnCode = code;
    }
    NSData *errorData = [[errorPipe fileHandleForReading] readDataToEndOfFile];
    NSString *stderrText = [[NSString alloc] initWithData:errorData encoding:NSUTF8StringEncoding];
    if (code != 0 && errorMessage) {
        NSString *trimmed = [stderrText stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
        *errorMessage = [trimmed length] > 0 ? trimmed : @"selection_cancelled";
    }
    return code == 0;
}

- (BOOL)captureScreenRectWithCoreGraphics:(NSRect)screenRect outputPath:(NSString *)outputPath errorMessage:(NSString **)errorMessage {
    NSScreen *targetScreen = nil;
    NSPoint center = NSMakePoint(NSMidX(screenRect), NSMidY(screenRect));
    for (NSScreen *screen in [NSScreen screens]) {
        if (NSPointInRect(center, [screen frame])) {
            targetScreen = screen;
            break;
        }
    }
    if (!targetScreen) {
        targetScreen = [NSScreen mainScreen] ?: [[NSScreen screens] firstObject];
    }
    if (!targetScreen) {
        if (errorMessage) {
            *errorMessage = @"No screen is available for capture.";
        }
        return NO;
    }

    NSRect screenFrame = [targetScreen frame];
    CGFloat scale = [targetScreen backingScaleFactor] > 0 ? [targetScreen backingScaleFactor] : 1.0;
    CGFloat localX = screenRect.origin.x - screenFrame.origin.x;
    CGFloat localY = screenRect.origin.y - screenFrame.origin.y;
    CGRect cropRect = CGRectMake(
        lround(localX * scale),
        lround((screenFrame.size.height - localY - screenRect.size.height) * scale),
        lround(screenRect.size.width * scale),
        lround(screenRect.size.height * scale)
    );
    if (cropRect.size.width < 1.0 || cropRect.size.height < 1.0) {
        if (errorMessage) {
            *errorMessage = @"Selected capture rectangle is too small.";
        }
        return NO;
    }

    NSNumber *screenNumber = [[targetScreen deviceDescription] objectForKey:@"NSScreenNumber"];
    CGDirectDisplayID displayID = (CGDirectDisplayID)[screenNumber unsignedIntValue];

    typedef CGImageRef (*CocoCGDisplayCreateImageFunc)(CGDirectDisplayID);
    CocoCGDisplayCreateImageFunc createImage = (CocoCGDisplayCreateImageFunc)dlsym(RTLD_DEFAULT, "CGDisplayCreateImage");
    if (!createImage) {
        if (errorMessage) {
            *errorMessage = @"Screen capture API is not available on this macOS runtime.";
        }
        return NO;
    }

    CGImageRef fullImage = createImage(displayID);
    if (!fullImage) {
        if (errorMessage) {
            *errorMessage = @"CGImage capture returned empty image.";
        }
        return NO;
    }

    CGFloat fullWidth = (CGFloat)CGImageGetWidth(fullImage);
    CGFloat fullHeight = (CGFloat)CGImageGetHeight(fullImage);
    if (fullWidth < 1.0 || fullHeight < 1.0) {
        CGImageRelease(fullImage);
        if (errorMessage) {
            *errorMessage = @"CGImage capture returned empty display image.";
        }
        return NO;
    }

    CGFloat minX = MAX(0.0, MIN(fullWidth - 1.0, cropRect.origin.x));
    CGFloat minY = MAX(0.0, MIN(fullHeight - 1.0, cropRect.origin.y));
    CGFloat maxX = MAX(minX + 1.0, MIN(fullWidth, cropRect.origin.x + cropRect.size.width));
    CGFloat maxY = MAX(minY + 1.0, MIN(fullHeight, cropRect.origin.y + cropRect.size.height));
    CGRect clampedCropRect = CGRectMake(lround(minX), lround(minY), lround(maxX - minX), lround(maxY - minY));

    [self appendCaptureBridgeLog:[NSString stringWithFormat:@"capture display=%u screenFrame=%.0f,%.0f,%.0f,%.0f pointRect=%.0f,%.0f,%.0f,%.0f cropRect=%.0f,%.0f,%.0f,%.0f full=%.0fx%.0f scale=%.2f",
                                  displayID,
                                  screenFrame.origin.x, screenFrame.origin.y, screenFrame.size.width, screenFrame.size.height,
                                  screenRect.origin.x, screenRect.origin.y, screenRect.size.width, screenRect.size.height,
                                  clampedCropRect.origin.x, clampedCropRect.origin.y, clampedCropRect.size.width, clampedCropRect.size.height,
                                  fullWidth, fullHeight,
                                  scale]];

    CGImageRef croppedImage = CGImageCreateWithImageInRect(fullImage, clampedCropRect);
    CGImageRelease(fullImage);
    BOOL ok = [self writeCGImage:croppedImage toPNGPath:outputPath errorMessage:errorMessage];
    if (croppedImage) {
        CGImageRelease(croppedImage);
    }
    return ok;
}

- (void)handleCaptureRequestAtPath:(NSString *)requestPath {
    NSData *data = [NSData dataWithContentsOfFile:requestPath];
    if (!data) {
        return;
    }
    NSDictionary *request = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
    if (![request isKindOfClass:[NSDictionary class]]) {
        [[NSFileManager defaultManager] removeItemAtPath:requestPath error:nil];
        return;
    }

    NSString *requestID = [request[@"request_id"] isKindOfClass:[NSString class]] ? request[@"request_id"] : [[requestPath lastPathComponent] stringByDeletingPathExtension];
    NSString *captureName = [request[@"capture_name"] isKindOfClass:[NSString class]] ? request[@"capture_name"] : [NSString stringWithFormat:@"capture_%@.png", requestID];
    if ([[captureName pathExtension] length] == 0) {
        captureName = [captureName stringByAppendingPathExtension:@"png"];
    }
    NSString *outputPath = [[self capturesPath] stringByAppendingPathComponent:[NSString stringWithFormat:@"native_%@_%@", requestID, [captureName lastPathComponent]]];

    self.captureBridgeBusy = YES;
    if (![self ensureScreenCaptureAccess]) {
        NSDictionary *deniedResult = @{
            @"request_id": requestID,
            @"status": @"permission_denied",
            @"return_code": @1,
            @"message": CocoCapturePermissionUserMessage,
            @"created_at": @([[NSDate date] timeIntervalSince1970])
        };
        [self writeCaptureResult:deniedResult requestID:requestID];
        [[NSFileManager defaultManager] removeItemAtPath:requestPath error:nil];
        self.captureBridgeBusy = NO;
        return;
    }

    [self appendCaptureBridgeLog:@"capture overlay started"];
    [self showCaptureOverlayWithCompletion:^(NSRect selectedRect, BOOL cancelled) {
        if (cancelled) {
            NSDictionary *cancelledResult = @{
                @"request_id": requestID,
                @"status": @"cancelled",
                @"return_code": @1,
                @"message": @"selection_cancelled",
                @"created_at": @([[NSDate date] timeIntervalSince1970])
            };
            [self writeCaptureResult:cancelledResult requestID:requestID];
            [[NSFileManager defaultManager] removeItemAtPath:requestPath error:nil];
            self.captureBridgeBusy = NO;
            [self appendCaptureBridgeLog:@"capture cancelled before image read"];
            return;
        }

        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSFileManager *fileManager = [NSFileManager defaultManager];
        NSString *internalMessage = @"";
        [self appendCaptureBridgeLog:[NSString stringWithFormat:@"capture coregraphics rect %.0f,%.0f,%.0f,%.0f", selectedRect.origin.x, selectedRect.origin.y, selectedRect.size.width, selectedRect.size.height]];
        BOOL captured = [self captureScreenRectWithCoreGraphics:selectedRect outputPath:outputPath errorMessage:&internalMessage];

        BOOL isDirectory = NO;
        BOOL outputExists = [fileManager fileExistsAtPath:outputPath isDirectory:&isDirectory] && !isDirectory;
        unsigned long long outputSize = 0;
        if (outputExists) {
            NSDictionary *attrs = [fileManager attributesOfItemAtPath:outputPath error:nil];
            outputSize = [attrs fileSize];
        }

        NSMutableDictionary *result = [NSMutableDictionary dictionary];
        result[@"request_id"] = requestID;
        result[@"return_code"] = captured ? @0 : @1;
        result[@"message"] = captured ? @"" : CocoCaptureFailureUserMessage;
        result[@"created_at"] = @([[NSDate date] timeIntervalSince1970]);
        if (captured && outputExists && outputSize > 0) {
            result[@"status"] = @"ok";
            result[@"path"] = outputPath;
            result[@"file_name"] = [outputPath lastPathComponent];
            [self appendCaptureBridgeLog:[NSString stringWithFormat:@"capture ok %@ size=%llu", outputPath, outputSize]];
        } else {
            if (outputExists) {
                [fileManager removeItemAtPath:outputPath error:nil];
            }
            result[@"status"] = @"error";
            [self appendCaptureBridgeLog:[NSString stringWithFormat:@"capture failed coregraphics message=%@", internalMessage ?: @""]];
        }

        [self writeCaptureResult:result requestID:requestID];
        [fileManager removeItemAtPath:requestPath error:nil];
        dispatch_async(dispatch_get_main_queue(), ^{
            [NSApp activateIgnoringOtherApps:YES];
            self.captureBridgeBusy = NO;
        });
        });
    }];
}

- (NSString *)splashHTML {
    return @"<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;width:100%;height:100%;background:#272934;color:#edf2ff;font-family:-apple-system,BlinkMacSystemFont,sans-serif}body{display:grid;place-items:center}.brand{font-size:42px;font-weight:800;color:#ff9b57}.brand span{color:#7aa8ff}.sub{margin-top:12px;color:#aab4ca;font-size:14px}</style></head><body><main><div class='brand'>COCO<span>AI</span></div><div class='sub'>CocoAi Study is starting.</div></main></body></html>";
}

- (void)startStreamlitAndLoad {
    NSString *resourcePath = [[NSBundle mainBundle] resourcePath];
    NSString *projectRoot = CocoBundleString(@"CocoProjectRoot", [resourcePath stringByAppendingPathComponent:@"project"]);
    NSString *pythonBin = CocoBundleString(@"CocoPythonBin", [[resourcePath stringByAppendingPathComponent:@"runtime"] stringByAppendingPathComponent:@"bin/python"]);
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
    environment[@"COCO_NATIVE_CAPTURE_BRIDGE"] = @"1";
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
