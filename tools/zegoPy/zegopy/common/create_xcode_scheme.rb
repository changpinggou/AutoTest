require 'xcodeproj'

xcode_proj_path = ARGV[0]
scheme_name = ARGV[1]

proj = Xcodeproj::Project.open(xcode_proj_path)
target = proj.targets.find { |item| item.to_s == scheme_name }

scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(target)
scheme.set_launch_target(target)
scheme.save_as(proj.path, scheme_name)

proj.save
